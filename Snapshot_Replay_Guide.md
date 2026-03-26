# ChatDev 快照/复现/混合 三模式指南

## 模式总览

| 模式 | CLI 参数 | 用途 |
|------|---------|------|
| **Snapshot** | (默认) | 正常运行，自动 Git 追踪 + JSONL 录制 |
| **Replay** | `--replay <jsonl>` | 零 API 消耗复现，从快照中匹配 input 返回 output |
| **Hybrid** | `--hybrid <jsonl> --hybrid-node <N>` | 前 N 个节点复现，第 N 个节点开始调用真实 API |

---

## 1. Snapshot 快照模式（默认）

每次 API 请求自动：
1. `git add . && git commit` 保存代码快照
2. 追加 `{timestamp, node_index, model, config, input, output}` 到 `api_records.jsonl`

```bash
python run.py --task "..." --name "MyApp"
```

产出物：`WareHouse/MyApp_.../api_records.jsonl`

---

## 2. Replay 复现模式

从已有快照零消耗还原整个运行过程。

```bash
python run.py --task "..." --name "MyApp" --replay "WareHouse/xxx/api_records.jsonl"
```

匹配策略：将当前 `messages` 的 `(role, content)` 与快照 `input` 做严格比对。

---

## 3. Hybrid 混合模式 🆕

**场景**：某次运行在第 N 个 API 调用处产生了不理想的结果，希望从这个节点重试。

```bash
# 前 15 个节点复现（node 0~14），第 15 个节点开始调用真实 API
python run.py --task "..." --name "MyApp" \
    --hybrid "WareHouse/xxx/api_records.jsonl" \
    --hybrid-node 15
```

**行为**：
1. **Node 0 ~ N-1**：Replay 模式，快照记录被**复制**到新 JSONL，**Git 全程提交**
2. **Node N 起**：Snapshot 模式，真实 API 调用，新结果追加到 JSONL
3. 最终得到一个**完整的新 `api_records.jsonl`**（前半段复制 + 后半段新生成）
4. 比如jsonl文件中总共14条记录，希望只修改最后一个节点，那么--hybrid-node=13
---

## 环境变量参考

| 变量 | 说明 |
|------|------|
| `CHATDEV_REPLAY_JSONL` | Replay 模式的源 JSONL 路径 |
| `CHATDEV_HYBRID_JSONL` | Hybrid 模式的源 JSONL 路径 |
| `CHATDEV_HYBRID_NODE` | Hybrid 切换节点索引 (0-based) |
| `CHATDEV_WORKSPACE` | 当前工作区路径（由 chat_chain.py 自动设置） |

## 快速体验

```bash
# 先 Snapshot 生成快照
python run.py --task "Create a CLI word counter." --name "WordCounter"

# 纯 Replay（零消耗）
python run.py --task "Create a CLI word counter." --name "WordCounter" \
    --replay "WareHouse/WordCounter_.../api_records.jsonl"

# Hybrid：从第 10 个节点重试
python run.py --task "Create a CLI word counter." --name "WordCounter" \
    --hybrid "WareHouse/WordCounter_.../api_records.jsonl" --hybrid-node 10
```
