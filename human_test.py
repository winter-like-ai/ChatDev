import os
from dotenv import load_dotenv

load_dotenv()

test = os.getenv("DEEPSEEK_API_KEY")
print(test)

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
    instruction="中国的首都是哪里？",
    context="答案写入.txt文件中",
))

print(result.action_type)    # ActionType.CODE_GENERATION
print(result.action_content) # 生成的代码文件内容

# 4. 导出内部轨迹日志（用于安全对齐分析）
logs = adapter.get_internal_logs()
for entry in logs:
    print(f"[{entry.phase_name}] {entry.agent_role}: {entry.content[:80]}")