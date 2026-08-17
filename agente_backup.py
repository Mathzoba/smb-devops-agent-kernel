from tool_postgres_query import PostgresQueryTool
from dotenv import load_dotenv
from groq import Groq
from kernel.config import settings
from kernel.agent import Agent
from kernel.schemas import Finding
import json

load_dotenv()


class AgenteBackup(Agent):
    def perceive(self) -> dict:
        tool = PostgresQueryTool()
        dados = tool.run(
            query=(
                "SELECT id, criado_em, servico, status, detalhe "
                "FROM backups ORDER BY criado_em DESC LIMIT 10;"
            )
        )
        return {"backups": dados["linhas"]}

    def plan(self, contexto: dict) -> dict:
        backups = contexto["backups"]
        texto_backups = "\n".join(
            f"- {backup['servico']}: {backup['status']} ({backup['detalhe']}, em {backup['criado_em']})"
            for backup in backups
        )

        client = Groq(api_key=settings.GROQ_API_KEY)
        resposta = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente de verificação de backups de TI. "
                        "Analise os backups e responda SOMENTE em JSON, exatamente neste formato: "
                        '{"causa_provavel": "...", "confianca": "baixa|media|alta", "proxima_acao": "..."}'
                    ),
                },
                {"role": "user", "content": texto_backups},
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
    agente = AgenteBackup(nome="Agente de Backup")
    agente.run()