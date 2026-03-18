import argparse
import os
import sys

# 导入 ChatDev 项目中已经封装好的 API 配置模块（支持自动切换 DeepSeek）
from agent_adapter.api_config import create_openai_client, get_model_name

def summarize_log(log_path):
    if not os.path.exists(log_path):
        print(f"错误: 找不到文件 '{log_path}'")
        sys.exit(1)
        
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
        sys.exit(1)
        
    print(f"已加载日志 '{log_path}' (共 {len(content)} 字符)。正在调用 DeepSeek API 进行总结...")
    
    try:
        # 使用项目中配置好的客户端，它会自动读取 .env 中的 DEEPSEEK_API_KEY 或者 OPENAI_API_KEY
        client = create_openai_client()
        
        # 传递标准名称，get_model_name 会自动帮你转换为 'deepseek-chat' (如果检测到 DEEPSEEK)
        model = get_model_name("gpt-4o") 
        
        # 防止日志超出 token 上限，截取最后 80,000 个字符（大概 20k~30k token）
        max_chars = 80000 
        if len(content) > max_chars:
            print(f"警告: 文件过长，截取最后 {max_chars} 个字符。")
            content = content[-max_chars:]

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system", 
                    "content": "你是一个资深的软件开发助手。请总结提供给你的运行日志文件（log file）。请说明主要执行了哪些任务（如哪些 Phase，哪些角色对话）、是否遇到了错误或异常、以及最终的运行结果（如生成了哪些代码文件等），使用清晰的中文回答。"
                },
                {
                    "role": "user", 
                    "content": f"这是日志文件的内容:\n\n{content}"
                }
            ],
            temperature=0.3
        )
        
        summary = response.choices[0].message.content
        print("\n" + "="*60)
        print("📋 日志总结")
        print("="*60)
        print(summary)
        print("="*60)
        
    except Exception as e:
        print(f"调用 API 时发生错误: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用 DeepSeek API 总结日志文件")
    parser.add_argument("log_file", help="要总结的 .log 文件的路径")
    args = parser.parse_args()
    
    summarize_log(args.log_file)
