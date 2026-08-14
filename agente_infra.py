import os
import requests
from dotenv import load_dotenv
from groq import Groq

from kernel.agent import Agent

load_dotenv()


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

        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente de monitoramento de infraestrutura. "
                        "Analise o status dos alvos monitorados abaixo e aponte se "
                        "há algo preocupante. Seja direto e curto."
                    ),
                },
                {"role": "user", "content": texto_alvos},
            ],
        )
        return {"sugestao": resposta.choices[0].message.content}

    def act(self, plano: dict) -> None:
        print("=" * 50)
        print(f"[{self.nome}] SUGESTÃO PENDENTE DE APROVAÇÃO HUMANA:")
        print(plano["sugestao"])
        print("=" * 50)
        self.registrar_sugestao(plano["sugestao"])


if __name__ == "__main__":
    agente = AgenteInfra(nome="Agente de Infraestrutura")
    agente.run()