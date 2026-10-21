import requests
from kernel.tools import Tool
from kernel.config import settings


class PrometheusUpTool(Tool):
    """
    Tool generica: consulta o metric 'up' do Prometheus e devolve o status
    de cada alvo monitorado (job, instance, ativo/caido).
    """

    def __init__(self):
        super().__init__(nome="prometheus_up")

    def run(self) -> dict:
        resposta = requests.get(
            f"{settings.PROMETHEUS_URL}/api/v1/query",
            params={"query": "up"},
            timeout=5,
        )
        resposta.raise_for_status()
        dados = resposta.json()

        alvos = []
        for item in dados["data"]["result"]:
            alvos.append({
                "job": item["metric"]["job"],
                "instance": item["metric"]["instance"],
                "status": "ativo" if item["value"][1] == "1" else "caido",
            })
        return {"alvos": alvos}