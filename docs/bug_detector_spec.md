# Bug Detector 故障检测模块 — 形式化规范

> 基于 `chatdev/analyzer/bug_detector.py` (当前 HEAD)
> 目标读者：需要理解故障定义、定位逻辑和评分公式的开发者

---

## 目录

1. [整体架构：两阶段流水线](#1-整体架构两阶段流水线)
2. [输入数据模型](#2-输入数据模型)
3. [故障类型的形式化定义](#3-故障类型的形式化定义)
4. [第一阶段：Claim 提取（LLM 降维器）](#4-第一阶段claim-提取llm-降维器)
5. [第二阶段：评分算法（算法法官）](#5-第二阶段评分算法算法法官)
   - [5.1 规范合规评分 FM-1.1 / FM-1.2](#51-规范合规评分-fm-11--fm-12)
   - [5.2 重复/死锁评分 FM-1.3](#52-重复死锁评分-fm-13)
   - [5.3 支持度评分（幻觉/漂移）FM-2.2 / FM-2.3](#53-支持度评分幻觉漂移-fm-22--fm-23)
   - [5.4 计划—动作对齐评分 FM-2.6（预留）](#54-计划动作对齐评分-fm-26预留)
6. [日志定位：从原始日志到故障坐标](#6-日志定位从原始日志到故障坐标)
7. [复合健康评分](#7-复合健康评分)
8. [预留扩展点](#8-预留扩展点)
9. [大模型 API 调用详情](#9-大模型-api-调用详情)
   - [9.1 OpenAI 客户端初始化](#91-openai-客户端初始化)
   - [9.2 Embedding API 调用](#92-embedding-api-调用)
   - [9.3 Claim 提取 API 调用 (Chat Completion)](#93-claim-提取-api-调用-chat-completion)
   - [9.4 完整流水线 API 调用图](#94-完整流水线-api-调用图)
   - [9.5 成本估算](#95-成本估算)
   - [9.6 环境变量参考](#96-环境变量参考)

---

## 1. 整体架构：两阶段流水线

```
原始 Agent 输出（非结构化文本）
         │
         ▼
┌─────────────────────────┐
│  Step 1: ClaimExtractor │   "LLM 大脑" — 语义编译器
│  extract_claims(text)   │   剥离社交噪音，提取原子声明
└───────────┬─────────────┘
            │  List[Claim]
            ▼
┌─────────────────────────┐
│  Step 2: ClaimScorer    │   "算法法官" — 向量计算器
│  - compute_support      │   每个 Claim 独立打分
│  - compute_norm         │   不判定，只展示分数
│  - compute_repetition   │
│  - plan_action_align    │
└───────────┬─────────────┘
            │  InteractionScores
            ▼
┌─────────────────────────┐
│  BugDetector (编排器)    │   遍历 Playbook，汇总统计
│  analyze_playbook()     │   输出 ScoredPlaybook
└─────────────────────────┘
```

**设计原则**：第一阶段用 LLM 做语义降维，第二阶段用纯算法做无偏评分。LLM 没有"判断权"，算法没有"解释权"——两者职责严格分离。

---

## 2. 输入数据模型

### 2.1 Playbook 结构

BugDetector 的入口是 `playbook.json`，由 `convert_to_playbook.py` 从 `api_records.jsonl` + 解析后的结构化日志生成：

```
playbook.json = {
    "<RoleName>": [
        {
            "turn":       int,     // 该角色的递增轮次 (1-based)
            "phase":      str,     // 所属阶段名称
            "phase_turn": int,     // 阶段内轮次
            "prompt":     str,     // 该轮给 Agent 的 prompt
            "output":     str,     // Agent 的输出
        },
        ...
    ],
    ...
}
```

### 2.2 核心数据结构

```
Claim:
    claim_id: int       // 声明序号
    action:   str       // 原子动作/决策的文本描述

SupportScoreDetail:
    claim_id:             int       // 对应 Claim
    claim_text:           str       // Claim 原文
    best_support_context: str       // 历史上下文中最匹配的句子
    grounded_score:       float     // 0~1，越高越有上下文依据

NormScoreDetail:
    rule:       str                 // 约束规则原文
    pass_score: float               // cos_sim(output, "遵守: rule")
    fail_score: float               // cos_sim(output, "违反: rule")
    score:      float               // pass_score - fail_score, >0 = 合规

InteractionScores:                  // 单轮交互的全部评分
    role, playbook_turn, phase, phase_turn, node_index
    claims:                          List[Claim]
    support_score_details:           List[SupportScoreDetail]
    aggregate_support_score:         float   // FM-2.2/2.3
    norm_score_details:              List[NormScoreDetail]
    aggregate_norm_score:            float   // FM-1.1/1.2
    repetition_score:                float   // FM-1.3
    repetition_reference_turn:       int
    overall_health_score:            float   // composite

ScoredPlaybook:                     // 整个 playbook 的评分汇总
    interactions:                   List[InteractionScores]
    support_score_mean/min:         float   // FM-2.2/2.3
    norm_score_mean/min:            float   // FM-1.1/1.2
    repetition_score_mean/max:      float   // FM-1.3
    health_score_mean/min:          float   // composite
    per_role_summary:               Dict[str, Dict]
```

---

## 3. 故障类型的形式化定义

### 3.1 规范/权限/契约破坏 (FM-1.1 + FM-1.2)

**形式化定义**：

> 给定 prompt 中声明的约束集合 $C = \{c_1, c_2, \ldots, c_n\}$ 和 Agent 输出 $O$，
> 在向量空间 $\mathbb{R}^d$ 中，为每个约束 $c_i$ 构造一对锚点：
>
> - **合规锚点** $v_i^+ = E(\text{"Obey these rules: } c_i\text{"})$
> - **违规锚点** $v_i^- = E(\text{"Don't obey these rules: } c_i\text{"})$
>
> 输出向量 $v_O = E(O)$。
>
> **偏差量** $\Delta_i = \cos(v_O, v_i^+) - \cos(v_O, v_i^-)$
>
> **判定**：若 $\Delta_i < \tau_{\text{norm}}$（默认 $\tau_{\text{norm}} = 0.05$），则该约束被判定为**违反**。
>
> $\Delta_i$ 的语义：
> - $\Delta_i > 0$：输出更接近"遵守规则"的语义方向 → 合规
> - $\Delta_i \approx 0$：输出在遵守与违反之间无显著偏向 → 模糊
> - $\Delta_i < 0$：输出更接近"违反规则"的语义方向 → 违规

**典型症状**：
- 输出格式不符合 prompt 要求的 JSON/Markdown 结构
- Agent 擅自终止任务或跳过必要步骤
- 跨 Agent 规范不一致导致下游执行错误
- 否定指令（"不要做 X"）被忽略

### 3.2 重复/死锁级联 (FM-1.3)

**形式化定义**：

> 给定当前轮输出 $O_t$ 和最近 $k$ 轮历史输出 $\{O_{t-1}, O_{t-2}, \ldots, O_{t-k}\}$，
>
> **重复度** $R_t = \max_{j \in [1, k]} \cos\big(E(O_t), E(O_{t-j})\big)$
>
> **判定**：若 $R_t > 1 - \delta_{\text{rep}}$（默认 $\delta_{\text{rep}} = 0.005$，对应 $R_t > 0.995$），则判定为**重复/死锁**。
>
> $R_t \in [0, 1]$，其中 $R_t = 0$ 表示全新内容，$R_t = 1$ 表示与某历史输出完全一致。

**典型症状**：
- 重复调用同参数工具/API
- 连续多轮生成语义相同的错误响应
- 多 Agent 并发下出现"互相等待/相互触发重试"

### 3.3 目标漂移/幻觉 (FM-1.5 + FM-2.2 + FM-2.3)

**形式化定义**：

> 给定当前输出中提取的声明集合 $\mathcal{A} = \{a_1, a_2, \ldots, a_m\}$ 和**初始任务描述** $T$（分割为句子集合 $\mathcal{S} = \{s_1, s_2, \ldots, s_p\}$），
>
> 对每个声明 $a_i$：
> - **支持度** $G(a_i) = \max_{s_j \in \mathcal{S}} \cos\big(E(a_i), E(s_j)\big)$
>
> **聚合支持度** $G_{\text{agg}} = \min_{a_i \in \mathcal{A}} G(a_i)$（最弱声明原则）
>
> **判定**：若 $G_{\text{agg}} < \tau_{\text{support}}$（默认 $\tau_{\text{support}} = 0.5$），则判定为**幻觉/漂移**。
>
> $G(a_i) \in [0, 1]$，其中 $G(a_i) = 0$ 表示声明与初始任务完全无关（完全幻觉/严重漂移），$G(a_i) = 1$ 表示与初始任务高度一致。

**典型症状**：
- 面对模糊指令臆测需求
- 对话中偏离主线、讨论无关细节
- Agent 输出中包含从未出现在 prompt/上下文中的"虚构事实"
- 多轮后与初始目标相似度逐级下降

### 3.4 计划—动作断裂 (FM-2.6)（预留接口）

**形式化定义**（预留，算法已实现但暂未纳入主流水线）：

> 给定计划步骤集合 $\mathcal{P} = \{p_1, p_2, \ldots, p_q\}$ 和执行动作文本 $a$，
>
> **对齐度** $A(a, \mathcal{P}) = \max_{p_i \in \mathcal{P}} \cos\big(E(a), E(p_i)\big)$
>
> **判定**：若 $A(a, \mathcal{P}) < \tau_{\text{align}}$，则计划与执行之间存在断裂。
>
> $A \in [0, 1]$，$A = 0$ 表示动作与所有计划步骤无关，$A = 1$ 表示完美对齐。

**典型症状**：
- 推理链声称要查天气，实际却调用计算器
- 计划步骤未执行 / 执行了计划外动作
- 下游无法追溯 action 对应哪个 plan step

---

## 4. 第一阶段：Claim 提取（LLM 降维器）

### 4.1 目的

将非结构化的 Agent 输出（包含社交噪音、代码块、情感表达）压缩为干净的原子声明列表。

### 4.2 LLM 模式 (`ClaimExtractor`)

**Prompt 设计**：

```
You are an objective semantic compiler. Read the following text from a multi-agent system output.

Ignore all thanks, pleasantries, emotional expressions, and social chatter.
Extract every substantive operation, API call, business conclusion, code action,
or meaningful decision as an independent "Atomic Claim".

Return strictly a JSON array with no extra text:
[{"claim_id": 1, "action": "the atomic action or decision described"}, ...]

If there are no substantive claims, return an empty array: []
```

**输入限制**：输出文本截断至 8000 字符。

**容错解析**：`_parse_claim_json()` 先用 `json.loads()` 直接解析；若失败则用正则 `\[.*\]` 提取 JSON 数组片段再解析；若仍然失败返回空列表。

### 4.3 快速模式 (`extract_claims_fast`)

不依赖 LLM，通过纯文本处理提取声明：

1. **代码块过滤**（`_remove_code_keep_comments`）：移除 markdown 代码块（```` ``` ```` 包裹区域），但保留其中的注释行（`#`, `//`, `/*`）作为自然语言信号。
2. **格式规范化**：将列表标记（`-`, `*`, 数字编号, `#` 标题）替换为句号；将多个连续换行替换为句号；将所有换行替换为空格。
3. **句子切分**（`_split_into_sentences`）：按标点 `. ! ?` 切分，过滤掉长度 ≤ 60 字符的短句（通常是社交寒暄/噪声）。

返回 `[Claim(claim_id=i, action=sentence) for each sentence]`。

### 4.4 两种模式的权衡

| 维度 | LLM 模式 | 快速模式 |
|------|---------|---------|
| 提取质量 | 高（理解语义） | 中（仅依赖标点和长度） |
| 速度 | 慢（API 调用） | 快（纯文本处理） |
| 成本 | 消耗 token | 零成本 |
| 适用场景 | 精确分析 | 快速扫描、批量预处理 |

默认使用 LLM 模式（`BugDetector(use_llm_extraction=True)`）。如需快速扫描可切换为快速模式（`BugDetector(use_llm_extraction=False)`），使用纯文本句子分割替代 LLM 调用。

---

## 5. 第二阶段：评分算法（算法法官）

所有评分基于 embedding 向量间的余弦相似度。Embedding 模型默认为 `text-embedding-3-small`（1536 维），带本地内存缓存（LRU 淘汰，上限 15000 条）。

### 5.1 规范合规评分 FM-1.1 / FM-1.2

#### 约束规则提取

`_extract_rules_from_prompt(prompt)` 从 prompt 中提取约束规则：

1. 匹配规则前缀的行：`- `、`* `、`数字. `
2. 包含强制关键词的行：`must`, `should`, `require`, `not`, `always`, `never`
3. 排除元指令行：包含 `"here is the task"` 或 `"according to"` 的行

#### 锚点偏差算法 (`ClaimScorer.compute_norm_scores`)

```
输入: output_text, rules

for each rule in rules:
    // 构造对比锚点
    pos_str = "Obey these rules: " + rule
    neg_str = "Don't obey these rules: " + rule

    v_pos = E(pos_str)
    v_neg = E(neg_str)
    v_out = E(output_text)

    pass_score  = cos(v_out, v_pos)   // 输出与"合规"锚点的相似度
    fail_score  = cos(v_out, v_neg)   // 输出与"违规"锚点的相似度
    score       = pass_score - fail_score  // 偏差量 Δ

输出: (per_rule_details, aggregate_score)
      aggregate_score = min(all_scores)  // 最弱约束原则
```

**直觉**：如果输出在向量空间中更接近"遵守规则 X"而非"违反规则 X"，则 Δ > 0。Δ 的正负和大小直接反映合规程度。这是一种**相对比较**，避免了绝对阈值的校准问题。

### 5.2 重复/死锁评分 FM-1.3

#### 滑动窗口相似度 (`ClaimScorer.compute_repetition_score`)

```
输入: current_output, past_outputs (最近 k 轮)

v_curr = E(current_output)

max_sim = -1.0
ref_idx = -1

for i, past in enumerate(past_outputs):
    if past is empty: skip
    v_past = E(past)
    sim = cos(v_curr, v_past)
    if sim > max_sim:
        max_sim = sim
        ref_idx = i

输出: (repetition_score, reference_index)
      repetition_score = max(0, max_sim)  // 截断负值
```

参数 `repetition_window = 3`（默认），即只比较最近 3 轮。

向后兼容函数 `scan_playbook_for_bug_1_3` 使用的是另一种 **k 连续窗口检查**：

```
for each position i where i + k ≤ n:
    base_vec = E(output_i)
    is_stuck = True
    for j = 1 to k:
        if 1 - cos(base_vec, E(output_{i+j})) ≥ distance_threshold:
            is_stuck = False; break
    if is_stuck:
        report bug at position i
```

### 5.3 支持度评分（幻觉/漂移）FM-2.2 / FM-2.3

#### 声明-任务匹配 (`ClaimScorer.compute_support_scores`)

```
输入: claims (声明列表), task_prompt (初始任务描述)

// Step 1: 将初始任务描述切分为句子
context_sentences = split_into_sentences(task_prompt)

if no context_sentences:
    return perfect_score for all claims

// Step 2: 批量获取 embedding
claim_embs  = E_batch([c.action for c in claims])
context_embs = E_batch(context_sentences)

// Step 3: 对每个声明，找与任务最匹配的句子
for each claim, claim_vec:
    max_sim = max(cos(claim_vec, c_vec) for c_vec in context_embs)
    best_context = argmax cos(claim_vec, c_vec)

输出: (per_claim_details, aggregate_score)
      aggregate_score = min(all_scores)  // 最弱声明原则
```

**最弱声明原则**：聚合分数取所有声明中的最小值。这确保即使大部分声明与任务高度一致，只要有任一声明偏离了初始目标（潜在漂移），就会被标记。

向后兼容接口 `check_hallucination_bug()` 支持 `aggregation in {'min', 'max', 'average'}` 三种聚合策略，但主流水线统一使用 `min`。

### 5.4 计划—动作对齐评分 FM-2.6（预留）

#### 动作-计划最大相似度 (`ClaimScorer.compute_plan_action_alignment`)

```
输入: plan_steps (计划步骤列表), action_text (执行动作文本)

v_action = E(action_text)
v_plans  = E_batch(plan_steps)

alignment = max(cos(v_action, v_plan) for v_plan in v_plans)

输出: alignment_score ∈ [0, 1]
```

当前状态：算法已实现，但在 BugDetector 主流水线中**未调用**。`InteractionScores` 中尚无对应字段。此评分器预留供后续 `ErrorLocator` 层使用。

---

## 6. 日志定位：从原始日志到故障坐标

### 6.1 完整定位链路

```
原始 .log 文件
    │
    ▼ [LogParser.parse()]
结构化 .json (events 数组)
    │
    ├──▶ api_records.jsonl (ChatDev 运行时自动生成)
    │         │
    │         ▼ [convert_to_playbook.api_to_playbook()]
    │    playbook.json (角色分组、按轮次排列)
    │         │
    │         ▼ [BugDetector.analyze_playbook()]
    │    ScoredPlaybook (每轮 InteractionScores)
    │         │
    │         ▼ [save_scored_playbook()]
    │    scored_playbook.json
    │
    └──▶ 直接使用向后兼容接口:
         scan_playbook_for_bug_1_1 / 1_3 / 2_2
              │
              ▼
         bug_reports (含坐标信息)
```

### 6.2 故障坐标体系

每个故障报告包含以下定位信息：

| 坐标字段 | 含义 | 来源 |
|---------|------|------|
| `role` | 产生输出的 Agent 角色名 | playbook key |
| `playbook_turn` | 该角色下的轮次编号 | playbook[role][i].turn |
| `phase` | 执行阶段名称 | agent_message.phase_name |
| `phase_turn` | 阶段内轮次 | agent_message.turn |
| `node_index` | api_records.jsonl 中的行号 (1-based) | `_find_node_index()` 匹配 |

### 6.3 Node Index 解析 (`_find_node_index`)

```
输入: api_records_path, prompt, output, matched_indices (已匹配行号集合)

// 取 output 前 100 字符作为匹配前缀
target_prefix = output[:min(100, len(output))]

// 遍历 api_records.jsonl 每一行
for line_number, line in enumerate(api_records, start=1):
    if line_number already matched: skip
    record = json.loads(line)
    record_output = record.output.choices[0].message.content
    if record_output starts with target_prefix:
        mark line_number as matched
        return line_number

输出: node_index (未找到返回 -1)
```

### 6.4 使用示例

```python
from chatdev.analyzer.bug_detector import BugDetector, save_scored_playbook

# 完整流水线
detector = BugDetector(use_llm_extraction=True)
scored = detector.analyze_playbook(
    "dataset_mini/project/playbook.json",
    "dataset_mini/project/api_records.jsonl"
)

# 查看每轮评分
for ix in scored.interactions:
    print(f"[{ix.role}] Turn {ix.playbook_turn} ({ix.phase}): "
          f"health={ix.overall_health_score:.3f}, "
          f"support(FM-2.2/2.3)={ix.aggregate_support_score:.3f}, "
          f"norm(FM-1.1/1.2)={ix.aggregate_norm_score:+.3f}, "
          f"rep(FM-1.3)={ix.repetition_score:.3f}")

# 保存完整评分
save_scored_playbook(scored, "output/scored.json")

# 或使用向后兼容的单 Bug 扫描
from chatdev.analyzer.bug_detector import scan_playbook_for_bug_1_1

bugs = scan_playbook_for_bug_1_1(
    "path/to/playbook.json",
    "path/to/api_records.jsonl"
)
for bug in bugs:
    print(f"Bug at role={bug['role']}, turn={bug['playbook_turn']}, "
          f"node={bug['node_index']}")
```

---

## 7. 复合健康评分

每个交互的**整体健康分** $H_t$ 是三个子评分的加权组合：

$$H_t = 0.35 \cdot S_{\text{support}} + 0.35 \cdot \frac{N_{\text{norm}} + 1}{2} + 0.30 \cdot (1 - R_{\text{rep}})$$

其中：
- $S_{\text{support}} \in [0, 1]$：支持度（越高越好）
- $N_{\text{norm}} \in [-1, 1]$：规范合规度（需映射到 $[0, 1]$）
- $R_{\text{rep}} \in [0, 1]$：重复度（越低越好，取反）

$H_t \in [0, 1]$，$H_t = 1$ 表示完美健康，$H_t = 0$ 表示严重故障。

**权重设计理念**：
- 支持度（35%）和规范（35%）等权——幻觉和违规同等危险
- 重复度（30%）略低——重复不一定是故障（可能是合理重试），需结合其他信号判断

---

## 8. 预留扩展点

### 8.1 `ErrorLocator`（错误定位层）

已声明但未实现。设计意图：
- 消费 `InteractionScores`，识别哪些具体 Claim 存在问题
- 将 Claim 映射到错误类别
- 产出包含证据片段的轮次级诊断

### 8.2 `ErrorClassifier`（错误分类层）

已声明但未实现。设计意图：
- 消费 `ErrorLocator` 的输出
- 分配故障模式编码（1.1–3.3）
- 产出带严重程度的结构化错误报告
- 支持跨运行的自动回归检测

### 8.3 计划-动作对齐接入

`ClaimScorer.compute_plan_action_alignment()` 已实现但未被主流水线调用。接入时需：
1. 在 `InteractionScores` 中新增 `plan_action_alignment_score` 字段
2. 在 `BugDetector.analyze_interaction()` 中注入计划步骤并调用
3. 在 `ScoredPlaybook` 统计中纳入对齐分

---

## 9. 大模型 API 调用详情

本章详述模块涉及的所有 LLM API 调用：OpenAI 客户端初始化、环境变量发现、Embedding API 的批处理与缓存策略、Claim 提取的 Chat Completion API 参数，以及完整分析流水线的 API 调用量估算。

### 9.1 OpenAI 客户端初始化

#### 环境变量加载 (`_load_env`)

模块导入时自动执行 `_load_env()`，按以下优先级搜索 `.env` 文件：

```
搜索起点:
  1. os.getcwd()                          // 当前工作目录
  2. os.path.dirname(os.path.abspath(__file__))  // bug_detector.py 所在目录

从每个起点向上递归遍历父目录，直到找到 .env 或到达文件系统根。
找到的第一个 .env 即为加载目标。
```

**加载策略（二级 fallback）**：

```
优先: python-dotenv
  from dotenv import load_dotenv
  load_dotenv(path, override=True)   // override=True 覆盖已存在的环境变量

回退: 手动解析
  for line in .env:
      if '=' in line and not line.startswith('#'):
          key, value = line.split('=', 1)
          os.environ[key.strip()] = value.strip()
```

#### 客户端构造

```python
from openai import OpenAI

# BASE_URL 解析优先级:
#   BASE_URL 环境变量 > OPENAI_BASE_URL 环境变量
effective_base_url = os.environ.get("BASE_URL") or os.environ.get("OPENAI_BASE_URL")

_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=effective_base_url     // None 时使用 OpenAI 默认地址
)
```

**必需环境变量**：

| 变量 | 用途 | 缺失时行为 |
|------|------|----------|
| `OPENAI_API_KEY` | API 认证密钥 | 客户端仍可构造，但调用会失败 |
| `BASE_URL` 或 `OPENAI_BASE_URL` | API 端点地址 | 使用 OpenAI 官方默认地址 `https://api.openai.com/v1` |

**全局单例**：`_client` 是模块级全局变量，整个进程生命周期内共享一个连接实例。不提供连接池或重试配置——依赖 `openai` 库的默认行为。

---

### 9.2 Embedding API 调用

**API**: `POST /v1/embeddings`（通过 `_client.embeddings.create`）

**模型**: `text-embedding-3-small`（默认，可通过 `ClaimScorer(embedding_model=...)` 覆盖）

**向量维度**: 1536

#### 单个文本 (`get_embedding`)

```python
def get_embedding(text: str, model="text-embedding-3-small") -> np.ndarray:
    return get_embeddings_batch([text], model=model)[0]
```

内部走批处理路径，batch_size=1。

#### 批处理 (`get_embeddings_batch`)

```
输入: texts: List[str], model: str

// Step 1: 预处理与缓存查询
results = []
to_fetch = []
for each text in texts:
    cleaned = text.replace("\n", " ").strip()
    if cleaned == "":
        results.append(np.zeros(1536))   // 空文本 → 零向量
    elif cleaned in _EMBEDDING_CACHE:
        results.append(_EMBEDDING_CACHE[cleaned])  // 缓存命中
    else:
        to_fetch.append(cleaned)
        results.append(None)              // 标记待填充

// Step 2: 分块请求（每块最多 500 条）
CHUNK_SIZE = 500
for each chunk in to_fetch split by CHUNK_SIZE:
    response = _client.embeddings.create(
        input=chunk,           // List[str], 最多 500 条
        model=model
    )
    embeddings = [np.array(d.embedding) for d in response.data]

// Step 3: 回填结果并写入缓存
for each None position in results:
    results[pos] = fetched_embeddings[fetch_idx]
    _EMBEDDING_CACHE[to_fetch[fetch_idx]] = fetched_embeddings[fetch_idx]
```

**批处理参数**：

| 参数 | 值 | 说明 |
|------|---|------|
| `CHUNK_SIZE` | 500 | 每次 API 调用的最大文本数 |
| 输入预处理 | `replace("\n", " ").strip()` | 换行替换为空格 |
| 空文本处理 | 返回零向量 `np.zeros(1536)` | 不消耗 API 调用 |

#### 本地缓存 (`_EMBEDDING_CACHE`)

```
类型: Dict[str, np.ndarray]
键:   清洗后的文本 (换行→空格, strip)
值:   1536 维 numpy 向量

淘汰策略: 简单 LRU
  if len(cache) > 15000:
      删除前 5000 个条目 (按插入顺序)
      实际效果: 保留最近 10000 条
```

**缓存命中率分析**：
- 同一 playbook 内：约束规则的锚点文本（`"Obey these rules: ..."`, `"Don't obey these rules: ..."`）跨轮次相同 → **高命中**
- 跨 playbook 批量分析：相同 prompt 模板的规则文本可复用 → **中等命中**
- 声明文本和上下文句子：通常每轮不同 → **低命中**

#### Embedding API 调用量估算

对于一次完整的 `BugDetector.analyze_playbook()`：

```
假设: N = 总交互轮数, C̄ = 每轮平均 claim 数, R̄ = 每轮平均规则数
      S̄ = 任务描述的句子数, W_rep = 3 (repetition_window)

每轮 API 调用:
  // compute_support_scores (Step 2a) — 与初始任务比较, S̄ 全局恒定
  Embedding 调用数 = ceil((C̄ + S̄) / 500)

  // compute_norm_scores (Step 2b)
  Embedding 调用数 = ceil((1 + 2*R̄) / 500)   // 1 个 output + 2*R̄ 个锚点

  // compute_repetition_score (Step 2c)
  Embedding 调用数 = ceil((1 + min(W_rep, past_turns)) / 500)

  // Claim extraction (Step 1) — 仅 LLM 模式
  若 use_llm_extraction=True: 1 次 Chat Completion API 调用

总计 (快速模式):
  总 Embedding 调用数 ≈ sum over N rounds of above
  最坏情况: 每轮 <= 3 次 Embedding 调用 (因为单轮文本量通常远小于 500)
  典型: 每轮 2~3 次 Embedding 调用

总计 (LLM 模式):
  额外增加 N 次 Chat Completion 调用
```

---

### 9.3 Claim 提取 API 调用 (Chat Completion)

**API**: `POST /v1/chat/completions`（通过 `_client.chat.completions.create`）

**仅在 `use_llm_extraction=True` 时触发**（默认开启）。设为 `False` 时使用快速文本分割模式替代。

#### 请求参数

```python
response = self.client.chat.completions.create(
    model=self.model,          // 默认 "gpt-4o"，可通过环境变量 CLAIM_EXTRACTOR_MODEL 或构造函数参数覆盖
    messages=[
        {"role": "system", "content": _CLAIM_EXTRACTION_PROMPT},
        {"role": "user",   "content": truncated_output}
    ],
    temperature=0.0,           // 零温度确保确定性输出
)
```

| 参数 | 值 | 说明 |
|------|---|------|
| `model` | `"gpt-4o"` (默认) | 可通过 `CLAIM_EXTRACTOR_MODEL` 环境变量覆盖 |
| `temperature` | `0.0` | 完全确定性输出，确保可复现 |
| `max_tokens` | 不限制（默认） | 依赖模型自身的输出长度限制 |
| `messages[0]` | system prompt | 语义编译器指令（见 4.2 节） |
| `messages[1]` | user message | Agent 输出文本（截断至 8000 字符） |

#### System Prompt 原文

```
You are an objective semantic compiler. Read the following text
from a multi-agent system output.

Ignore all thanks, pleasantries, emotional expressions, and
social chatter.
Extract every substantive operation, API call, business conclusion,
code action, or meaningful decision as an independent
"Atomic Claim".

Return strictly a JSON array with no extra text:
[{"claim_id": 1, "action": "the atomic action or decision described"}, ...]

If there are no substantive claims, return an empty array: []
```

#### 响应处理

```
正常路径:
  content = response.choices[0].message.content
  claims = _parse_claim_json(content)

异常路径 (任意 Exception):
  claims = extract_claims_fast(output_text)   // 回退到快速模式
```

#### `_parse_claim_json` 容错链

```
第一次尝试: json.loads(raw_response.strip())
  成功 → 返回 List[Claim]
  失败 ↓

第二次尝试: re.search(r'\[.*\]', raw_response, re.DOTALL)
  匹配 → json.loads(match.group(0)) → 返回 List[Claim]
  无匹配 ↓

最终回退: return []   // 空列表，该轮 claims 数为 0，所有 support scores 为 perfect
```

#### Token 消耗估算

| 组件 | 近似 token 数 |
|------|-------------|
| System prompt | ~100 tokens |
| User message (max) | ~2500 tokens (8000 字符 ≈ 2500 tokens) |
| 输出 (JSON array) | ~200–1000 tokens (取决于 claim 数量) |
| **每次调用总计** | **~500–3000 tokens** |

---

### 9.4 完整流水线 API 调用图

```
analyze_playbook(playbook_path, api_records_path)
│
├─ _extract_task_prompt(playbook) → task_prompt (首个非空 prompt)
├─ for each role in playbook:
│   └─ for each interaction in role:
│       └─ analyze_interaction(prompt, output, task_prompt, past_outputs, ...)
│           │
│           ├─ Step 1: extract_claims(output)
│           │   ├─ [LLM mode]      1 × Chat Completion (gpt-4o, temp=0)
│           │   └─ [Fast mode]     0 API calls (纯文本处理)
│           │
│           ├─ Step 2a: compute_support_scores(claims, task_prompt)
│           │   └─ get_embeddings_batch([claims..., task_sentences...])
│           │       └─ ceil((|claims| + |task_sentences|) / 500) × Embedding API
│           │
│           ├─ Step 2b: compute_norm_scores(output, rules)
│           │   └─ get_embedding(output)  ─┐
│           │   └─ for each rule:          ├─ 合并为一次批处理
│           │       get_embedding(pos_str)  │  ceil((1 + 2|rules|) / 500)
│           │       get_embedding(neg_str) ─┘  × Embedding API
│           │
│           └─ Step 2c: compute_repetition_score(output, past_outputs)
│               └─ get_embeddings_batch([output] + past_outputs)
│                   └─ ceil((1 + |past|) / 500) × Embedding API
│
└─ 汇总统计 (纯 CPU 计算, 无 API 调用)
```

**注意**：当前实现中各评分器的 embedding 调用是**独立的**——即同一轮内 `output` 文本可能被多次送入 Embedding API。缓存（`_EMBEDDING_CACHE`）在跨轮次时能减轻重复，但同一轮内的重复查询依赖 Python dict 的精确键匹配。

---

### 9.5 成本估算

以一次典型的 ChatDev 运行（约 20 轮交互，4 个角色）为例：

**快速模式 (默认)**：

| API | 每轮调用次数 | 20 轮总计 | 单价 (approx) | 总成本 (approx) |
|-----|------------|----------|--------------|----------------|
| Embedding API | 2–3 次 | 40–60 次 | $0.02 / 1M tokens | < $0.01 |

**LLM 模式**：

| API | 每轮调用次数 | 20 轮总计 | 单价 (approx) | 总成本 (approx) |
|-----|------------|----------|--------------|----------------|
| Embedding API | 2–3 次 | 40–60 次 | $0.02 / 1M tokens | < $0.01 |
| Chat Completion (gpt-4o) | 1 次 | 20 次 | $2.50 / 1M input, $10 / 1M output | ~$0.15–$0.30 |

**批量分析** (`analyze_playbooks_batch`)：成本线性增长，但 embedding 缓存跨 playbook 有效，可减少实际 API 调用。

---

### 9.6 环境变量参考

模块导入时读取以下环境变量：

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI/兼容 API 密钥 | 无（必需） |
| `BASE_URL` | API 端点地址（优先级高） | `https://api.openai.com/v1` |
| `OPENAI_BASE_URL` | API 端点地址（优先级低） | `https://api.openai.com/v1` |
| `CLAIM_EXTRACTOR_MODEL` | Claim 提取的 LLM 模型 | `gpt-4o` |

推荐的 `.env` 文件位置：项目根目录或 `chatdev/analyzer/` 目录。

---

## 附录 A：评分一览

| 评分名称 | 简称 | 范围 | 最优 | 所属故障 | 计算方式 |
|---------|------|------|------|---------|---------|
| Support Score | support | [0, 1] | 1.0 | FM-2.2/2.3 | max cos(claim, context) |
| Norm Score | norm | [-1, 1] | 1.0 | FM-1.1/1.2 | Δ = cos(+,out) − cos(−,out) |
| Repetition Score | rep | [0, 1] | 0.0 | FM-1.3 | max cos(current, past) |
| Plan-Action Alignment | align | [0, 1] | 1.0 | FM-2.6 (预留) | max cos(action, plan) |
| Health Score | health | [0, 1] | 1.0 | — | 0.35×support + 0.35×norm_mapped + 0.30×(1−rep) |

## 附录 B：关键阈值

| 参数 | 默认值 | 用途 | 关联函数 |
|------|-------|------|---------|
| `threshold` (norm) | 0.05 | Norm Score 低于此值判定违规 | `check_constraint_violation` |
| `threshold` (hallucination) | 0.5 | Support Score 低于此值判定幻觉 | `check_hallucination_bug` |
| `distance_threshold` (rep) | 0.005 | 1−similarity 高于此值判定不重复 | `scan_playbook_for_bug_1_3` |
| `repetition_window` | 3 | 重复检查窗口大小 | `BugDetector.__init__` |
| `max_chars` (LLM extraction) | 8000 | 送入 LLM 的最大字符数 | `ClaimExtractor.extract_claims` |
