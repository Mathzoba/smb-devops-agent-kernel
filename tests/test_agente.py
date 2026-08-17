from kernel.agent import Agent


class AgenteFalso(Agent):
    def __init__(self):
        super().__init__(nome="Agente Falso")
        self.chamadas = []

    def perceive(self) -> dict:
        self.chamadas.append("perceive")
        return {}

    def plan(self, contexto: dict) -> dict:
        self.chamadas.append("plan")
        return {}

    def act(self, plano: dict) -> None:
        self.chamadas.append("act")


def test_run_chama_perceive_plan_act_em_ordem():
    agente = AgenteFalso()
    agente.run()
    assert agente.chamadas == ["perceive", "plan", "act"]