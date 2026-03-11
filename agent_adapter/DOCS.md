# `agent_adapter` 模块文档

> **版本**：1.0.0 | **Python**：≥ 3.12 | **依赖**：`pydantic>=2.0`, `python-dotenv`, `openai`

本包为 ChatDev 多智能体框架提供标准化的 **Benchmark 接入适配层**，将任意底层智能体系统（单体 LLM 或多智能体框架）封装为统一接口，供外部自动化评测引擎调用。

---

## 目录

- [包结构](#包结构)
- [快速开始](#快速开始)
- [模块：`api_config`](#模块api_config)
- [模块：`models`](#模块models)
- [模块：`exceptions`](#模块exceptions)
- [模块：`base`](#模块base)
- [模块：`chatdev_adapter`](#模块chatdev_adapter)
- [环境变量参考](#环境变量参考)
- [DeepSeek 模型映射表](#deepseek-模型映射表)
- [异常层次结构](#异常层次结构)

---

## 包结构

```
agent_adapter/
├── __init__.py          # 包入口，导出所有公共 API
├── api_config.py        # 统一 API Key / Base URL 配置（支持 OpenAI / DeepSeek）
├── models.py            # Pydantic v2 数据模型（输入/输出/日志/错误）
├── exceptions.py        # 标准化异常层次
├── base.py              # 抽象基类 AgentAdapterBase
├── chatdev_adapter.py   # ChatDev 具体适配器实现
└── DOCS.md              # 本文档
```

---

## 快速开始

### 使用 ChatDev 适配器

```python
from agent_adapter import ChatDevAdapter, ObservationInput

# 1. 实例化适配器（DeepSeek API Key 已写入 .env 文件）
adapter = ChatDevAdapter(
    config="Default",          # CompanyConfig/ 下的配置名
    model="DEEPSEEK_CHAT",     # 支持 OpenAI / DeepSeek 模型
    org_name="BenchmarkOrg",
)

# 2. 每次新任务前重置会话（强制隔离）
adapter.reset_session(task_id="benchmark_task_001")

# 3. 执行任务（底层多轮协作完全封装）
result = adapter.act(ObservationInput(
    instruction="开发一个命令行版 2048 游戏",
    context="目标平台：Python 3.12+，无 GUI",
))

print(result.action_type)    # ActionType.CODE_GENERATION
print(result.action_content) # 生成的代码文件内容

# 4. 导出内部轨迹日志（用于安全对齐分析）
logs = adapter.get_internal_logs()
for entry in logs:
    print(f"[{entry.phase_name}] {entry.agent_role}: {entry.content[:80]}")
```

### 自定义适配器

```python
from agent_adapter import AgentAdapterBase, ObservationInput, ActionOutput, ActionType
from agent_adapter.models import InternalLogEntry

class MyCustomAdapter(AgentAdapterBase):
    """包装自定义智能体系统"""

    def reset_session(self, task_id: str, **kwargs) -> None:
        # 清空内部状态
        self.my_internal_state = {}
        super().reset_session(task_id, **kwargs)  # 必须调用

    def act(self, observation: ObservationInput) -> ActionOutput:
        self._check_session()  # 检查会话是否已初始化
        # 调用底层智能体逻辑...
        result_text = my_agent.run(observation.instruction)
        self._log_event("MyPhase", "MyAgent", "response", result_text)
        return ActionOutput(
            action_type=ActionType.TEXT_RESPONSE,
            action_content=result_text,
        )

    def get_internal_logs(self) -> list[InternalLogEntry]:
        return list(self._internal_logs)
```

---

## 模块：`api_config`

**文件**：[`api_config.py`](./api_config.py)

统一管理 API Key 和 Base URL，支持 OpenAI / DeepSeek 自动回退。通过 `python-dotenv` 从项目根目录的 `.env` 文件加载密钥。

### Key Resolution 优先级

```
1. OPENAI_API_KEY 环境变量存在  →  使用 OpenAI（BASE_URL 可选覆盖）
2. DEEPSEEK_API_KEY 存在（.env 或环境变量）  →  自动切换到 DeepSeek
3. 均不存在  →  EnvironmentError（附带详细说明）
```

### 枚举

#### `APIProvider`

| 值 | 含义 |
|---|---|
| `OPENAI` | 使用 OpenAI API |
| `DEEPSEEK` | 使用 DeepSeek API |
| `UNKNOWN` | 未检测到可用 Key |

### 函数

#### `get_provider() -> APIProvider`

获取当前活跃的 API 提供商。若无可用 Key，抛出 `EnvironmentError`。

---

#### `get_api_key() -> str`

获取当前可用的 API Key 字符串。

```python
from agent_adapter.api_config import get_api_key
key = get_api_key()  # 自动选择 OPENAI_API_KEY 或 DEEPSEEK_API_KEY
```

---

#### `get_base_url() -> Optional[str]`

获取 API Base URL。

- OpenAI 模式：返回 `BASE_URL` 环境变量（若设置），否则 `None`（SDK 默认）
- DeepSeek 模式：返回 `"https://api.deepseek.com"`（或 `BASE_URL` 覆盖值）

---

#### `get_model_name(original_model: str) -> str`

将模型名称映射为当前提供商对应的实际模型名。

```python
# OpenAI 模式
get_model_name("gpt-4o")        # → "gpt-4o"

# DeepSeek 模式
get_model_name("gpt-4o")        # → "deepseek-chat"
get_model_name("deepseek-chat") # → "deepseek-chat"（透传）
```

---

#### `get_max_tokens_for_model(model_name: str) -> int`

返回指定模型的最大 Token 数（已映射后的名称）。未知模型默认返回 `4096`。

---

#### `create_openai_client() -> openai.OpenAI`

创建并返回一个已配置好 API Key 和 Base URL 的 OpenAI 客户端实例，可直接用于调用。

```python
from agent_adapter.api_config import create_openai_client
client = create_openai_client()
response = client.chat.completions.create(...)
```

---

#### `print_api_status()`

调试用。打印当前提供商、脱敏 Key、以及 Base URL。

---

### 常量

| 常量 | 值 | 说明 |
|------|----|------|
| `DEEPSEEK_BASE_URL` | `"https://api.deepseek.com"` | DeepSeek 默认端点 |
| `DEEPSEEK_MODEL_MAP` | `dict[str, str]` | OpenAI → DeepSeek 模型映射表 |
| `DEEPSEEK_MAX_TOKEN_MAP` | `dict[str, int]` | DeepSeek 模型 Token 限制 |

---

## 模块：`models`

**文件**：[`models.py`](./models.py)

使用 **Pydantic v2** 定义 Benchmark 引擎与适配器之间的数据契约，提供严格的字段校验和 JSON 序列化/反序列化支持。

### `ObservationInput`

Benchmark 引擎传递给适配器的标准化观测输入。

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `instruction` | `str` | ✅ | 当前指令/题目（不可为空字符串） |
| `context` | `Optional[str]` | | 环境背景、约束条件等 |
| `history` | `Optional[list[dict]]` | | 历史交互，每条含 `role` 和 `content` |
| `metadata` | `Optional[dict]` | | 扩展元数据（task_id、difficulty 等） |

```python
obs = ObservationInput(
    instruction="开发贪吃蛇游戏",
    context="Python 3.12+，使用 curses 库",
    history=[{"role": "user", "content": "请开始"}],
    metadata={"task_id": "t001", "difficulty": "medium"},
)
```

---

### `ActionOutput`

适配器返回给 Benchmark 引擎的标准化动作输出。

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `action_type` | `ActionType` | ✅ | 动作类别枚举 |
| `action_content` | `str` | ✅ | 具体动作内容 |
| `confidence` | `Optional[float]` | | 置信度 0.0～1.0 |
| `metadata` | `Optional[dict]` | | 附加元数据（文件列表、耗时等） |

---

### `ActionType` *(Enum)*

| 值 | 含义 |
|----|------|
| `TEXT_RESPONSE` | 纯文本回复 |
| `BASH_COMMAND` | Shell 命令 |
| `FILE_EDIT` | 文件编辑 |
| `CODE_GENERATION` | 代码生成（多文件） |
| `NO_ACTION` | 无动作（错误/超时/拒绝） |

---

### `ErrorResponse`

错误状态的标准化描述，通常嵌入在 `ActionOutput.metadata["error"]` 中。

| 字段 | 类型 | 说明 |
|------|------|------|
| `error_code` | `str` | 错误编码，如 `"TokenLimitExceededError"` |
| `error_message` | `str` | 人类可读的错误描述 |
| `error_type` | `ErrorType` | 错误类别枚举 |
| `is_recoverable` | `bool` | 重试是否可能成功 |

---

### `ErrorType` *(Enum)*

| 值 | 含义 | 可恢复 |
|----|------|:---:|
| `TOKEN_LIMIT_EXCEEDED` | Token 超限 | ✅ |
| `SAFETY_FILTER_TRIGGERED` | 安全审查拦截 | ❌ |
| `INTERNAL_ERROR` | 内部组件崩溃 | ❌ |
| `TIMEOUT` | 超时 | ✅ |
| `UNKNOWN` | 未知错误 | ❌ |

---

### `InternalLogEntry`

内部轨迹日志条目，用于安全对齐和效率分析，不参与 Benchmark 评分。

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | `str` | ISO 格式时间戳（自动生成） |
| `phase_name` | `str` | 所属阶段，如 `"Coding"`, `"CodeReview"` |
| `agent_role` | `str` | 智能体角色，如 `"Programmer"`, `"CTO"` |
| `event_type` | `str` | 事件类型，如 `"chat_message"`, `"phase_complete"` |
| `content` | `str` | 事件内容 |
| `metadata` | `Optional[dict]` | 附加元数据 |

---

## 模块：`exceptions`

**文件**：[`exceptions.py`](./exceptions.py)

定义适配器层的异常层次，用于将底层系统的各类错误标准化，防止评测进程崩溃。

### `AgentAdapterError`

**所有适配器异常的基类。**

```python
AgentAdapterError(message="...", original_error=None)
```

| 属性 | 类型 | 说明 |
|------|------|------|
| `message` | `str` | 错误描述 |
| `original_error` | `Exception \| None` | 原始底层异常（调试用） |

---

### `TokenLimitExceededError(AgentAdapterError)`

Token 使用量超出模型上限时抛出。**可恢复（重试）**。

```python
raise TokenLimitExceededError(token_used=20000, token_limit=16384)
```

| 额外属性 | 类型 | 说明 |
|---------|------|------|
| `token_used` | `int` | 实际使用量 |
| `token_limit` | `int` | 模型上限 |

---

### `SafetyFilterTriggeredError(AgentAdapterError)`

请求被内容安全策略拦截时抛出。**不可恢复**。

```python
raise SafetyFilterTriggeredError(filter_reason="content_policy_violation")
```

| 额外属性 | 类型 | 说明 |
|---------|------|------|
| `filter_reason` | `str` | 触发过滤的原因描述 |

---

### `InternalComponentError(AgentAdapterError)`

底层系统某内部组件崩溃时抛出。**不可恢复**。

```python
raise InternalComponentError(component_name="ChatChain", original_error=e)
```

| 额外属性 | 类型 | 说明 |
|---------|------|------|
| `component_name` | `str` | 发生故障的组件名称 |

---

### `SessionNotInitializedError(AgentAdapterError)`

在 `reset_session()` 之前调用 `act()` 时抛出。**可恢复（先调用 reset_session）**。

---

## 模块：`base`

**文件**：[`base.py`](./base.py)

定义 `AgentAdapterBase` 抽象基类，规范所有适配器必须实现的 4 大核心接口。

### `AgentAdapterBase` *(ABC)*

#### 抽象方法（子类必须实现）

---

##### `reset_session(task_id: str, **kwargs) -> None`

为每次新任务重置内部状态，确保任务间**绝对物理/逻辑隔离**。

> 子类实现时，**必须在最后调用 `super().reset_session(task_id, **kwargs)`**，
> 以触发：`_session_initialized = True`、`_current_task_id = task_id`、`_internal_logs.clear()`。

```python
def reset_session(self, task_id: str, **kwargs) -> None:
    # 清理底层资源...
    super().reset_session(task_id, **kwargs)  # 必须调用
```

---

##### `act(observation: ObservationInput) -> ActionOutput`

核心交互接口。将底层所有内部协作**封装为单次输入→单次输出**，使 Benchmark 无法感知内部细节。

> 建议通过 `safe_act()` 替代直接调用，可自动获得异常捕获。

---

##### `get_internal_logs() -> list[InternalLogEntry]`

导出内部轨迹日志列表（按时间顺序）。用于安全对齐分析，不参与评分。

---

#### 具体方法（可直接使用）

---

##### `safe_act(observation: ObservationInput) -> ActionOutput`

带完整容错保护的 `act()` 包装器。**永远不会抛出异常**。

自动处理：
1. 会话初始化检查
2. 底层异常捕获
3. 返回标准化 `NO_ACTION` 错误输出

```python
result = adapter.safe_act(obs)  # 推荐使用，替代直接调用 act()
```

---

##### `aact(observation: ObservationInput) -> ActionOutput` *(async)*

异步版本，默认将 `act()` 包装进线程池执行，避免阻塞事件循环。子类可覆写提供真正的异步实现。

```python
result = await adapter.aact(obs)
```

---

##### `_handle_error(error: AgentAdapterError) -> ActionOutput`

将适配器异常转换为标准化 `NO_ACTION` 输出，同时写入内部日志。Benchmark 会收到格式化的 `ErrorResponse` 而非崩溃。

---

##### `_log_event(phase_name, agent_role, event_type, content, metadata=None)`

向内部日志缓冲追加一条事件记录。子类在执行底层逻辑时调用此方法记录关键步骤。

---

##### `_check_session()`

若会话未初始化则抛出 `SessionNotInitializedError`。在 `act()` 开头调用。

---

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `session_initialized` | `bool` | 当前会话是否已初始化 |
| `current_task_id` | `str \| None` | 当前任务 ID |

---

## 模块：`chatdev_adapter`

**文件**：[`chatdev_adapter.py`](./chatdev_adapter.py)

`ChatDevAdapter` 的具体实现，将 ChatDev 的完整多角色软件开发流水线封装为标准适配器接口。

### `ChatDevAdapter(AgentAdapterBase)`

#### 构造函数

```python
ChatDevAdapter(
    config: str = "Default",
    model: str = "GPT_3_5_TURBO",
    org_name: str = "DefaultOrganization",
    chatdev_root: str | None = None,
)
```

| 参数 | 说明 |
|------|------|
| `config` | 配置名称，对应 `CompanyConfig/` 下子目录（如 `"Default"`） |
| `model` | 模型名称，支持 `"GPT_4O"`, `"DEEPSEEK_CHAT"`, `"DEEPSEEK_REASONER"` 等 |
| `org_name` | 组织名称，用于生成输出目录 |
| `chatdev_root` | ChatDev 项目根路径（默认自动检测） |

#### `act()` 内部执行流程

```
ObservationInput.instruction
        ↓
1. 初始化 ChatChain（加载配置、解析角色和阶段）
        ↓
2. pre_processing（清理目录、任务增强）
        ↓
3. make_recruitment（按配置招募智能体角色）
        ↓
4. execute_chain（按 chain 配置依次执行各 Phase，内含多轮角色对话）
   ├── DemandAnalysis（需求分析）
   ├── LanguageChoose（技术选型）
   ├── Coding（编码）
   ├── CodeReviewComment → CodeReviewModification（代码审查）
   ├── TestErrorSummary → TestModification（测试修复）
   ├── EnvironmentDoc（依赖文档）
   └── Manual（用户手册）
        ↓
5. post_processing（总结、日志归档）
        ↓
6. 收集 software_path 下的 .py 文件
        ↓
ActionOutput(action_type=CODE_GENERATION, action_content=<代码>)
```

#### 异常分类逻辑

`ChatDevAdapter` 的 `_classify_error()` 会根据底层异常消息自动分类：

| 关键词 | 映射异常 |
|--------|---------|
| `token`, `context_length`, `max_tokens` | `TokenLimitExceededError` |
| `content_policy`, `safety`, `harmful` | `SafetyFilterTriggeredError` |
| 其他 | `InternalComponentError(component_name="ChatChain")` |

---

## 环境变量参考

| 变量名 | 必填 | 说明 |
|--------|:---:|------|
| `OPENAI_API_KEY` | 二选一 | OpenAI API Key |
| `DEEPSEEK_API_KEY` | 二选一 | DeepSeek API Key（可写入 `.env` 文件） |
| `BASE_URL` | | 自定义 API 端点（可用于代理或中转站） |

**`.env` 文件示例（项目根目录）：**
```dotenv
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
# BASE_URL=https://your-proxy.com/v1
```

---

## DeepSeek 模型映射表

当使用 DeepSeek API 时，OpenAI 模型名称会自动映射：

| 原始名 | 映射后 |
|--------|--------|
| `gpt-3.5-turbo` / `gpt-3.5-turbo-16k` | `deepseek-chat` |
| `gpt-4` / `gpt-4-turbo` / `gpt-4o` / `gpt-4o-mini` | `deepseek-chat` |
| `deepseek-chat` | `deepseek-chat`（透传） |
| `deepseek-reasoner` | `deepseek-reasoner`（透传） |

**ChatDev CLI 使用 DeepSeek：**
```bash
python run.py --model DEEPSEEK_CHAT --task "Develop a calculator" --name Calc
python run.py --model DEEPSEEK_REASONER --task "Develop a sorting algorithm demo" --name SortDemo
```

---

## 异常层次结构

```
Exception
└── AgentAdapterError
    ├── TokenLimitExceededError       # Token 超限（可恢复）
    ├── SafetyFilterTriggeredError    # 安全审查拦截（不可恢复）
    ├── InternalComponentError        # 内部组件崩溃（不可恢复）
    └── SessionNotInitializedError    # 未初始化会话（可恢复）
```

**通用捕获示例：**
```python
from agent_adapter.exceptions import AgentAdapterError, TokenLimitExceededError

try:
    result = adapter.act(obs)
except TokenLimitExceededError as e:
    print(f"Token 超限: 已用 {e.token_used}/{e.token_limit}")
    # 可尝试裁剪上下文后重试
except AgentAdapterError as e:
    print(f"适配器错误: {e}")
    # 或直接使用 safe_act() 跳过手动 try/except
```

> **推荐**：始终使用 `adapter.safe_act(obs)` 替代 `adapter.act(obs)`，前者内置完整异常捕获，不会导致评测进程崩溃。
