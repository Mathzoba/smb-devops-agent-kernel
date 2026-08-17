import json
import requests
from groq import Groq
from kernel.config import settings
from kernel.schemas import Finding
from kernel.agent import Agent


class AgenteInfra(Agent):
    def perceive(self) -> dict:
        resposta = requests.get(
            "http://localhost:9090/api/v1/query",
            params={"query": "up"},
        )
        dados = resposta.json()

        alvos = []
        for item in dados["data"]["result"]:
            alvos.append({
                "job": item["metric"]["job"],
                "instance": item["metric"]["instance"],
                "status": "ativo" if item["value"][1] == "1" else "caido",
            })
        return {"alvos": alvos}

    def plan(self, contexto: dict) -> dict:
        alvos = contexto["alvos"]
        texto_alvos = "\n".join(
            f"- {a['job']} ({a['instance']}): {a['status']}" for a in alvos
        )

        client = Groq(api_key=settings.GROQ_API_KEY)
        resposta = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente de monitoramento de infraestrutura. "
                        "Analise o status dos alvos monitorados e responda SOMENTE em JSON, "
                        'exatamente neste formato: {"causa_provavel": "...", '
                        '"confianca": "baixa|media|alta", "proxima_acao": "..."}'
                    ),
                },
                {"role": "user", "content": texto_alvos},
            ],
        )
        dados = json.loads(resposta.choices[0].message.content)
        finding = Finding(
            causa_provavel=dados["causa_provavel"],
            confianca=dados["confianca"],
            proxima_acao=dados["proxima_acao"],
        )
        return {"finding": finding}

    def act(self, plano: dict) -> None:
        finding = plano["finding"]
        print("=" * 50)
        print(f"[{self.nome}] SUGESTÃO PENDENTE DE APROVAÇÃO HUMANA:")
        print(f"Causa provável: {finding.causa_provavel}")
        print(f"Confiança: {finding.confianca}")
        print(f"Próxima ação: {finding.proxima_acao}")
        print("=" * 50)
        self.registrar_sugestao(finding)


if __name__ == "__main__":
    agente = AgenteInfra(nome="Agente de Infraestrutura")
    agente.run()