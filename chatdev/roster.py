class Roster():
    def __init__(self) -> None:
        self.agents = list()

    def _recruit(self, agent_name: str):
        """招募员工进入花名册。"""
        self.agents.append(agent_name)

    def _exist_employee(self, agent_name: str):
        """检查员工是否已经存在于名单中。"""
        names = self.agents + [agent_name]
        names = [name.lower().strip() for name in names]
        names = [name.replace(" ", "").replace("_", "") for name in names]
        agent_name = names[-1]
        if agent_name in names[:-1]:
            return True
        return False

    def _print_employees(self):
        """打印所有招募的员工列表。"""
        names = self.agents
        names = [name.lower().strip() for name in names]
        print("Employees: {}".format(names))
