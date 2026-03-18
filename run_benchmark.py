# =========== Benchmark 集成运行脚本 ===========
# 演示如何将 Agent Adapter 与 Environment Adapter 结合
# 运行 ProgramDev 数据集中的任务
# ======================================================

import os
import sys
import logging
import argparse
from pprint import pprint

# 确保项目根目录在 python path 中
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 导入智能体端抽象与具体实现
from agent_adapter.models import ObservationInput, ActionType as AgentActionType
from agent_adapter.chatdev_adapter import ChatDevAdapter

# 导入环境端抽象与具体实现
from benchmark.env_adapter.models import ActionInput, ActionType as EnvActionType
from benchmark.env_adapter.programdev_env import ProgramDevEnv
from benchmark.env_adapter.exceptions import BenchmarkEnvironmentError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BenchmarkRunner")


def map_action(agent_action) -> ActionInput:
    """
    将智能体端的 ActionOutput 映射为环境端的 ActionInput。
    注意：两个体系共享相同的 ActionType 定义（名字和值一致）。
    """
    if not agent_action:
        return ActionInput(
            action_type=EnvActionType.NO_ACTION,
            action_content="无动作",
        )
    
    # 将智能体端的 ActionType 转换为环境端的 ActionType
    env_action_type = EnvActionType(agent_action.action_type.value)
    
    return ActionInput(
        action_type=env_action_type,
        action_content=agent_action.action_content,
        metadata=agent_action.metadata,
    )


def map_observation(env_observation) -> ObservationInput:
    """
    将环境端的 Observation 映射为智能体端的 ObservationInput。
    """
    if not env_observation:
        return ObservationInput(instruction="")
        
    return ObservationInput(
        instruction=env_observation.instruction,
        feedback=env_observation.feedback,
        current_files=env_observation.current_files,
        step_count=env_observation.step_count,
        metadata=env_observation.metadata,
    )


def run_benchmark_task(task_id: str, dataset_path: str = None):
    """
    运行完整的单个 Benchmark 任务。
    
    流程：
    1. 初始化 Environment (ProgramDevEnv) 和 Agent (ChatDevAdapter)
    2. Env.reset(task_id) -> 获得初始 obs
    3. 进入交互循环：
       - Agent.act(obs) -> 获得 action
       - Env.step(action) -> 获得新 obs, reward, done, info
    4. 当 done=True 时退出循环
    5. Env.evaluate() -> 获得指标，输出报告
    6. 自动清理资源 (通过 with 语句)
    """
    logger.info(f"=== 开始 Benchmark 任务评测: {task_id} ===")
    
    # 默认使用自带的 dataset
    if not dataset_path:
        dataset_path = os.path.join(
            _project_root, "benchmark", "programdev", "programdev_dataset.json"
        )
        
    # 初始化 ProgramDev 环境适配器并使用上下文管理器自动管资源
    try:
        with ProgramDevEnv(dataset_path=dataset_path) as env:
            # 1. 环境初始化
            env_obs = env.reset(task_id)
            
            # 从环境获取 project_name，作为 ChatDev 的任务和项目名称（例如 2048）
            project_name = env_obs.metadata.get("project_name", task_id) if env_obs.metadata else task_id
            
            # 初始化 ChatDev 智能体适配器
            agent = ChatDevAdapter()
            agent.reset_session(task_id=project_name)
            done = False
            total_reward = 0.0
            
            logger.info(f"环境已就绪。任务指令: {env_obs.instruction[:50]}...")
            
            # 2. 交互循环
            while not done:
                # 转换观测给智能体
                agent_obs = map_observation(env_obs)
                
                logger.info(f"--- 第 {env.step_count + 1} 步 ---")
                
                # 智能体思考和行动
                logger.info("智能体正在思考生成动作...")
                agent_action_out = agent.safe_act(agent_obs)
                
                logger.info(f"智能体动作: {agent_action_out.action_type.value}")
                
                # 转换动作给环境
                env_action_in = map_action(agent_action_out)
                
                # 环境推演状态
                logger.info("环境正在执行动作...")
                step_result = env.safe_step(env_action_in)
                
                env_obs = step_result.observation
                done = step_result.done
                total_reward += step_result.reward
                
                if env_obs.feedback:
                    logger.info(f"环境反馈: {env_obs.feedback[:100]}...")
            
            # 3. 评测结算
            logger.info("=== 交互结束，开始根据最终状态和沙盒验证进行综合评测 ===")
            metrics = env.evaluate()
            
            print("\n" + "="*50)
            print(f"🏆 评测报告: 任务 {task_id}")
            print("="*50)
            print(f"代码验证通过率 : {metrics.pass_rate:.2%}")
            print(f"是否能成功运行 : {'✅ 是' if metrics.runtime_success else '❌ 否'}")
            print(f"是否有语法错误 : {'❌ 是' if not metrics.compilation_success else '✅ 无'}")
            print(f"是否有安全警报 : {'⚠️ 是' if metrics.security_violation else '✅ 无'}")
            print(f"运行总耗时(ms) : {metrics.execution_time_ms:.2f}")
            print("-"*50)
            print("详情:")
            print(metrics.details)
            print("="*50)
            
    except BenchmarkEnvironmentError as e:
        logger.error(f"Benchmark 环境异常: {e}")
    except Exception as e:
        logger.error(f"运行过程发生未知异常: {e}", exc_info=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行 ChatDev Benchmark 评测")
    parser.add_argument(
        "--task", "-t", 
        type=str, 
        default="all", 
        help="要运行的任务标识符 (项目名如 'TicTacToe' 或数字索引如 '0')，输入 'all' 运行全部"
    )
    parser.add_argument(
        "--dataset", "-d", 
        type=str, 
        default=None, 
        help="指定数据集的 JSON 文件路径"
    )
    
    args = parser.parse_args()
    
    if args.task.lower() == "all":
        import json
        dataset_path = args.dataset
        if not dataset_path:
            dataset_path = os.path.join(
                _project_root, "benchmark", "programdev", "programdev_dataset.json"
            )
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                dataset = json.load(f)
            num_tasks = len(dataset)
            logger.info(f"开始顺序执行整个 Benchmark, 共 {num_tasks} 个任务。")
            for i in range(num_tasks):
                run_benchmark_task(str(i), dataset_path)
        except Exception as e:
            logger.error(f"加载数据集失败: {e}")
    else:
        run_benchmark_task(args.task, args.dataset)
