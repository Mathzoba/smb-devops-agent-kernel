import os
import psycopg2
from dotenv import load_dotenv
from groq import Groq

from kernel.agent import Agent

load_dotenv()


class AgenteTriagemIncidentes(Agent):
    def perceive(self) -> dict:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="demo",
            password="demo123",
            dbname="smb_demo",
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT id, criado_em, servico, severidade, mensagem "
            "FROM alertas ORDER BY criado_em DESC LIMIT 10;"
        )
        alertas = cur.fetchall()
        cur.close()
        conn.close()
        return {"alertas": alertas}

    def plan(self, contexto: dict) -> dict:
        alertas = contexto["alertas"]

        texto_alertas = "\n".join(
            f"- [{severidade}] {servico}: {mensagem} (em {criado_em})"
            for (_, criado_em, servico, severidade, mensagem) in alertas
        )

        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente de triagem de incidentes de TI. "
                        "Analise os alertas abaixo, aponte a causa provável mais "
                        "plausível e sugira um próximo passo. Seja direto e curto."
                    ),
                },
                {"role": "user", "content": texto_alertas},
            ],
        )
        return {"sugestao": resposta.choices[0].message.content}

    def act(self, plano: dict) -> None:
        print("=" * 50)
        print(f"[{self.nome}] SUGESTÃO PENDENTE DE APROVAÇÃO HUMANA:")
        print(plano["sugestao"])
        print("=" * 50)


if __name__ == "__main__":
    agente = AgenteTriagemIncidentes(nome="Agente de Triagem de Incidentes")
    agente.run()