# ChatDev 项目架构文档

ChatDev 是一个基于大语言模型（LLM）驱动的虚拟软件公司框架。多智能体在此框架内扮演不同角色（如 CEO、程序员、测试员等），通过协作完成软件开发任务。以下是该项目的主要目录名称及各文件/文件夹的功能说明：

## 核心源代码目录

### `chatdev/`
ChatDev 的核心业务逻辑和生命周期管理模块。
- **[chat_chain.py](file:///d:/Works/code/winter-like-ai/ChatDev/chatdev/chat_chain.py)**：定义了 `ChatChain` 类，负责整体的软件开发流程和智能体协作链。
- **[chat_env.py](file:///d:/Works/code/winter-like-ai/ChatDev/chatdev/chat_env.py)**：定义了环境上下文，管理开发过程中共享的环境变量、上下文信息和代码存储。
- **[phase.py](file:///d:/Works/code/winter-like-ai/ChatDev/chatdev/phase.py) / [composed_phase.py](file:///d:/Works/code/winter-like-ai/ChatDev/chatdev/composed_phase.py)**：定义了开发流程中的各个阶段（如需求分析、编码、测试等）及其组合行为。
- **[codes.py](file:///d:/Works/code/winter-like-ai/ChatDev/ecl/codes.py) / [documents.py](file:///d:/Works/code/winter-like-ai/ChatDev/chatdev/documents.py)**：代码和文档的数据结构和操作方法。
- **[eval_quality.py](file:///d:/Works/code/winter-like-ai/ChatDev/chatdev/eval_quality.py) / [statistics.py](file:///d:/Works/code/winter-like-ai/ChatDev/chatdev/statistics.py)**：用于评估生成代码架构以及统计项目指标。
- **[utils.py](file:///d:/Works/code/winter-like-ai/ChatDev/ecl/utils.py)**：通用工具函数。
- **[roster.py](file:///d:/Works/code/winter-like-ai/ChatDev/chatdev/roster.py)**：维护了各个角色的花名册。

### `camel/`
底层智能体和模型交互模块（基于 CAMEL-AI 框架的思想），用于处理信息收发和模型调用。
- **`agents/`**：定义了智能角色的具体行为机制（如角色模拟、响应生成）。
- **`messages/` / `prompts/`**：存储系统和角色的 prompt 模板定义，以及信息传递时的消息结构。
- **[model_backend.py](file:///d:/Works/code/winter-like-ai/ChatDev/camel/model_backend.py) / [generators.py](file:///d:/Works/code/winter-like-ai/ChatDev/camel/generators.py)**：大语言模型（OpenAI GPT等）的底层 API 调用封装和生成逻辑。
- **[human.py](file:///d:/Works/code/winter-like-ai/ChatDev/camel/human.py)**：支持“人机交互（Human-Agent-Interaction）”模式，允许人类扮演角色的逻辑。
- **[configs.py](file:///d:/Works/code/winter-like-ai/ChatDev/camel/configs.py) / [typing.py](file:///d:/Works/code/winter-like-ai/ChatDev/camel/typing.py)**：配置定义和类型提示约束。

### `ecl/`
经验共学（Experiential Co-Learning, ECL）模块，一个允许智能体利用过往经验改进新任务处理的高级特性。
- **[experience.py](file:///d:/Works/code/winter-like-ai/ChatDev/ecl/experience.py) / [ece.py](file:///d:/Works/code/winter-like-ai/ChatDev/ecl/ece.py)**：处理经验数据的记录与利用。
- **`memory/` / [memory.py](file:///d:/Works/code/winter-like-ai/ChatDev/ecl/memory.py)**：经验内存管理模块，实现智能体的记忆能力。
- **[graph.py](file:///d:/Works/code/winter-like-ai/ChatDev/ecl/graph.py) / [embedding.py](file:///d:/Works/code/winter-like-ai/ChatDev/ecl/embedding.py)**：图结构和向量化工具，用于检索或存储经验。

## 配置与运行相关目录

### `CompanyConfig/`
存放“虚拟公司”的各类运行配置文件。定义了公司中的工作流、阶段和角色系统。
- **`Default/`**：默认配置，包含基础的 ChatChain、Phase 和 Role 设定。
- **`Art/` / `Human/` / `Incremental/`**：针对特定模式（如自动绘图、人机交互、增量开发）的配置文件集。

### [run.py](file:///d:/Works/code/winter-like-ai/ChatDev/run.py)
项目的统一入口点。它接收命令行参数（如需求 `--task`、名称 `--name`、公司配置 `--config` 等），初始化运行环境和 `ChatChain`，并驱动整个开发链条启动。

## 产出与业务数据目录

### `WareHouse/`
“软件仓库”，存放系统每次运行后生成的项目产物。
- 每一个子目录（如 `2048_THUNLP_20230822144615/`）代表一次完整的生成记录，内部包含：
  - 生成的源代码文件和资源文件。
  - 项目 README。
  - 公司环境配置文件备份。
  - 详细的对话日志文件（`.log`）和初始需求记录（`.prompt`）。

### `visualizer/`
基于 Flask 的 Web 可视化工具模块，用于直观地回放或实时查看整个生成日志 (`.log` 文件) 以及架构。
- **[app.py](file:///d:/Works/code/winter-like-ai/ChatDev/visualizer/app.py)**：Web 应用程序的路由与启动文件。
- **`static/`** / `templates/`：前端静态资源（图片、脚本、样式表）及页面模板。

## 文档与资源目录

### `misc/`
杂项和多媒体附件。项目 [README.md](file:///d:/Works/code/winter-like-ai/ChatDev/README.md) 面向开发者展示时使用的各种图片、图表、演示动画、Logo（如 [intro.png](file:///d:/Works/code/winter-like-ai/ChatDev/misc/intro.png)、[logo1.png](file:///d:/Works/code/winter-like-ai/ChatDev/misc/logo1.png) 等）均放在这里。

### `readme/`
多语言 README 文件存储目录。包含了中文、日文、法文等各语种的说明文档，方便全球开发者了解项目。

### `MultiAgentEbook/`
关于大模型多智能体协作（LLM-powered multi-agent collaboration）相关的开放电子书资源、论文收录列表以及相关代码。

### `SRDD/`
软件需求文档设计（Software Requirement Document Design）相关的实验数据、图表和文档资料。属于研究分析文件。

## 环境和根目录文件

- **[README.md](file:///d:/Works/code/winter-like-ai/ChatDev/README.md) / [wiki.md](file:///d:/Works/code/winter-like-ai/ChatDev/wiki.md) / [Contribution.md](file:///d:/Works/code/winter-like-ai/ChatDev/Contribution.md)**：项目的使用指南、维基百科全书式的深入教程、社区贡献指南。
- **[requirements.txt](file:///d:/Works/code/winter-like-ai/ChatDev/requirements.txt) / `.conda`**：Python 环境依赖说明。
- **[Dockerfile](file:///d:/Works/code/winter-like-ai/ChatDev/Dockerfile)**：提供 Docker 容器化运行支持的环境配置文件。
