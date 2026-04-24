"""
cli.py - chatdev.analyzer 命令行入口

用法::

    # 单文件解析
    python -m chatdev.analyzer.cli input.log
    python -m chatdev.analyzer.cli input.log -o output.json

    # 批量解析
    python -m chatdev.analyzer.cli ./data/dataset_mini/ --batch
    python -m chatdev.analyzer.cli ./data/dataset_mini/ --batch -o ./results/

    # 选项
    python -m chatdev.analyzer.cli input.log --skip-flask --skip-http
    python -m chatdev.analyzer.cli input.log --validate
"""
import argparse
import io
import json
import os
import sys

# Windows GBK 控制台兼容：强制 UTF-8 输出
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser(
        prog="chatdev.analyzer",
        description="ChatDev 日志结构化解析工具：将 .log 文件转化为 JSON",
    )
    ap.add_argument(
        "input",
        help="输入路径：.log 文件（单文件模式）或目录（批量模式）",
    )
    ap.add_argument(
        "-o", "--output",
        default=None,
        help="输出路径：.json 文件（单文件）或目录（批量），默认同源路径",
    )
    ap.add_argument(
        "--batch",
        action="store_true",
        help="批量模式：递归解析目录下所有 .log 文件",
    )
    ap.add_argument(
        "--skip-flask",
        action="store_true",
        default=True,
        help="跳过 flask_not_start 事件（默认开启）",
    )
    ap.add_argument(
        "--no-skip-flask",
        action="store_true",
        help="不跳过 flask_not_start 事件",
    )
    ap.add_argument(
        "--skip-http",
        action="store_true",
        default=False,
        help="跳过 http_request 事件",
    )
    ap.add_argument(
        "--validate",
        action="store_true",
        help="解析后对输出进行 schema 验证",
    )

    args = ap.parse_args()

    # 延迟导入以避免循环依赖
    from . import LogParser, validate

    skip_flask = not args.no_skip_flask
    parser = LogParser(skip_flask=skip_flask, skip_http=args.skip_http)

    if args.batch:
        print(f"批量解析目录: {args.input}")
        results = parser.parse_batch(args.input, args.output)

        if args.validate:
            print("\n验证结果:")
            for i, result in enumerate(results):
                is_valid, errors = validate(result)
                name = result.get("metadata", {}).get("project_name", f"#{i}")
                if is_valid:
                    print(f"  [OK] {name}")
                else:
                    print(f"  [FAIL] {name}: {errors}")
    else:
        if not os.path.isfile(args.input):
            print(f"错误: 文件不存在 {args.input}", file=sys.stderr)
            sys.exit(1)

        print(f"解析文件: {args.input}")
        result = parser.parse(args.input, args.output)

        out_path = args.output or (os.path.splitext(args.input)[0] + ".json")
        print(f"输出文件: {out_path}")

        summary = result.get("summary", {})
        print(f"\n  事件总数:    {summary.get('total_events', '?')}")
        print(f"  API 调用数:  {summary.get('num_api_calls', '?')}")
        print(f"  总 Token:    {summary.get('total_tokens', '?')}")
        print(f"  总花费:      ${summary.get('total_cost', '?')}")
        print(f"  执行阶段:    {', '.join(summary.get('phases_executed', []))}")

        if args.validate:
            is_valid, errors = validate(result)
            if is_valid:
                print("\n  Schema 验证: [OK] 通过")
            else:
                print("\n  Schema 验证: [FAIL] 失败")
                for e in errors:
                    print(f"    - {e}")


if __name__ == "__main__":
    main()
