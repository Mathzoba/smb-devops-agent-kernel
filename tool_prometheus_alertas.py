import requests
from kernel.tools import Tool
from kernel.config import settings


class PrometheusAlertasTool(Tool):
    """
    Busca os alertas do Prometheus (somente leitura).
    Devolve so os alertas 'firing' (disparados de verdade).
    """

    def __init__(self):
        super().__init__(nome="prometheus_alertas")

    def run(self) -> dict:
        resposta = requests.get(f"{settings.PROMETHEUS_URL}/api/v1/alerts", timeout=5)
        resposta.raise_for_status()
        alertas = resposta.json()["data"]["alerts"]
        disparados = [a for a in alertas if a["state"] == "firing"]
        return {"alertas": disparados}