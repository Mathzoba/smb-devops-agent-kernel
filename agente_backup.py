import os
import psycopg2
from dotenv import load_dotenv
from groq import Groq

from kernel.agent import Agent

load_dotenv()


class AgenteBackup(Agent):
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
            "SELECT id, criado_em, servico, status, detalhe "
            "FROM backups ORDER BY criado_em DESC LIMIT 10;"
        )
        backups = cur.fetchall()
        cur.close()
        conn.close()
        return {"backups": backups}

    def plan(self, contexto: dict) -> dict:
        backups = contexto["backups"]

        texto_backups = "\n".join(
            f"- [{status}] {servico}: {detalhe} (em {criado_em})"
            for (_, criado_em, servico, status, detalhe) in backups
        )

        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente de verificação de backups de TI. "
                        "Analise os backups abaixo, aponte quais tiveram falha e "
                        "sugira um próximo passo pra cada um. Seja direto e curto."
                    ),
                },
                {"role": "user", "content": texto_backups},
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
    agente = AgenteBackup(nome="Agente de Backup")
    agente.run()