from kernel.agent import Agent


class AgenteExemplo(Agent):
    def perceive(self) -> dict:
        print(f"[{self.nome}] Percebendo o ambiente (ainda sem lógica real)...")
        return {}

    def plan(self, contexto: dict) -> dict:
        print(f"[{self.nome}] Planejando com base no contexto: {contexto}")
        return {}

    def act(self, plano: dict) -> None:
        print(f"[{self.nome}] Agindo com base no plano: {plano}")


if __name__ == "__main__":
    agente = AgenteExemplo(nome="Agente de Teste")
    agente.run()