经过分析项目源码，ChatDev 项目中共有 **3 个核心基础模块**直接调用了大模型的 API（底层都是调用了 `client.chat.completions.create` 或旧版接口）。这三个地方分管了不同的业务场景：

### 1. 核心沟通代理层（最重要的调用点）
**文件路径**：[camel/model_backend.py](cci:7://file:///d:/Works/code/winter-like-ai/ChatDev/camel/model_backend.py:0:0-0:0) 中的 `OpenAIModel.run()`
* **所属业务**：这里是 ChatDev 最**核心**的引擎。项目里所有角色的 Agent（如 CEO、程序员、测试员、代码审查员）之间的对话模拟、代码生成、逻辑推演，**全部**都会汇聚到这个函数中进行统一的 API 发包。
* **特点**：它是动态匹配的，不仅自适应 OpenAI 新旧版本 SDK，还支持动态读取外部配置的模型名（如 `gpt-3.5-turbo`, `gpt-4o` 等），而且我们刚刚为你新增的 Git 自动备份及 `api_records.jsonl` 日志功能就是注入在这个交通枢纽里面。

---

### 2. 网页爬虫辅助思考层（Web Spider）
**文件路径**：[camel/web_spider.py](cci:7://file:///d:/Works/code/winter-like-ai/ChatDev/camel/web_spider.py:0:0-0:0) 中的 [modal_trans()](cci:1://file:///d:/Works/code/winter-like-ai/ChatDev/camel/web_spider.py:54:0-88:17) 函数
* **所属业务**：当在 ChatDev 的主要配置设定中开启了 `web_spider: True` 时触发。
* **具体行为**：这个脚本在生成软件前，会悄悄调用两次大模型执行额外的网络知识抓取。
  1. 第一次调用大模型：让大模型从你输入的提示词（比如“写一个五子棋”）中提取出一个关键名词。
  2. 然后利用 Python 去爬取和检索维基百科/百度百科。
  3. 第二次调用大模型：让大模型把爬取到的维基百科超长文本进行知识总结，然后将其注入给 ChatDev 作为辅助开发的背景知识。
* **注意点**：这部分代码强制硬编码绑定了使用 `gpt-3.5-turbo-16k` 作为处理网络爬虫知识的模型。

---

### 3. ECL 评估/扩展工具层（独立副本）
**文件路径**：[ecl/utils.py](cci:7://file:///d:/Works/code/winter-like-ai/ChatDev/ecl/utils.py:0:0-0:0) 中的 `OpenAIModel.run()`
* **所属业务**：这是另一套极其相似的代码，推测是项目为了某些特定基准测试、或环境控制与评估程序（ECL 可能指 Evaluation / Execution Control Layer）而复制出来的一套独立工具。
* **特点**：独立于主线之外，有着自己独立的 [OpenAIModel](cci:2://file:///d:/Works/code/winter-like-ai/ChatDev/camel/model_backend.py:57:0-211:27) 类和 [calc_max_token](cci:1://file:///d:/Works/code/winter-like-ai/ChatDev/ecl/utils.py:52:0-72:36) 逻辑。它在发送 API 请求时（第 144 行）同样被硬编码为了 `model = "gpt-3.5-turbo-16k"`。

***

**总结来说**：你日常看到的核心交互 99% 都是通过 [camel/model_backend.py](cci:7://file:///d:/Works/code/winter-like-ai/ChatDev/camel/model_backend.py:0:0-0:0) 跑的，网络请求扩展通过 [camel/web_spider.py](cci:7://file:///d:/Works/code/winter-like-ai/ChatDev/camel/web_spider.py:0:0-0:0) 跑的，而 [ecl/utils.py](cci:7://file:///d:/Works/code/winter-like-ai/ChatDev/ecl/utils.py:0:0-0:0) 则作为独立的测试脚本挂载在项目里。