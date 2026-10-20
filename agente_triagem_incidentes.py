from tool_postgres_query import PostgresQueryTool
from dotenv import load_dotenv
from groq import Groq
from kernel.config import settings
from kernel.schemas import Finding, Evidence
from kernel.agent import Agent
import json
from tool_prometheus_query import PrometheusUpTool

load_dotenv()


# ---------- Funcoes puras: transformam dado em Evidence, sem banco/rede ----------

def alertas_para_evidencias(linhas: list[dict]) -> list[Evidence]:
    """Transforma linhas da tabela 'alertas' em evidencias. Funcao pura: nao acessa banco."""
    evidencias = []
    for alerta in linhas:
        evidencia = Evidence(
            tipo="alerta",
            fonte="postgres",
            timestamp=str(alerta["criado_em"]),
            assunto=alerta["servico"],
            observacao=f"[{alerta['severidade']}] {alerta['mensagem']}",
        )
        evidencias.append(evidencia)
    return evidencias


def alvos_para_evidencias(
    alvos: list[dict], servicos_alertados: list[str], coletado_em: str
) -> list[Evidence]:
    """Transforma alvos do Prometheus em evidencias e marca servicos alertados sem monitoramento."""
    evidencias = []

    for alvo in alvos:
        evidencias.append(Evidence(
            tipo="monitoramento",
            fonte="prometheus",
            timestamp=coletado_em,
            assunto=alvo["job"],
            observacao=f"alvo {alvo['instance']} esta {alvo['status']}",
        ))

    monitorados = {alvo["job"] for alvo in alvos}
    for servico in set(servicos_alertados):
        if servico not in monitorados:
            evidencias.append(Evidence(
                tipo="monitoramento",
                fonte="prometheus",
                timestamp=coletado_em,
                assunto=servico,
                observacao="servico nao aparece entre os alvos monitorados pelo Prometheus",
            ))

    return evidencias


# ---------- Agente ----------

class AgenteTriagemIncidentes(Agent):
    def perceive(self) -> dict:
        tool = PostgresQueryTool()
        dados = tool.run(
            query=(
                "SELECT id, criado_em, servico, severidade, mensagem "
                "FROM alertas ORDER BY criado_em DESC LIMIT 10;"
            )
        )
        return {"alertas": dados["linhas"]}

    def plan(self, contexto: dict) -> dict:
        alertas = contexto["alertas"]
        texto_alertas = "\n".join(
            f"- [{alerta['severidade']}] {alerta['servico']}: {alerta['mensagem']} (em {alerta['criado_em']})"
            for alerta in alertas
        )

        prometheus_tool = PrometheusUpTool()
        dados_prometheus = prometheus_tool.run()
        texto_prometheus = "\n".join(
            f"- {alvo['job']} ({alvo['instance']}): {alvo['status']}"
            for alvo in dados_prometheus["alvos"]
        )

        client = Groq(api_key=settings.GROQ_API_KEY)
        resposta = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente de triagem de incidentes de TI. "
                        "Analise os alertas abaixo. Você também recebe a lista de alvos "
                        "monitorados pelo Prometheus e seus status, como evidência adicional. "
                        "Se o serviço do alerta NÃO aparecer nessa lista, isso significa que não "
                        "há monitoramento confirmando ou contradizendo o alerta — diga isso "
                        "explicitamente na causa provável, e reduza a confiança de acordo. "
                        "Responda SOMENTE em JSON, exatamente neste formato: "
                        '{"causa_provavel": "...", "confianca": "baixa|media|alta", "proxima_acao": "..."}'
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Alertas:\n{texto_alertas}\n\n"
                        f"Status no Prometheus:\n{texto_prometheus}"
                    ),
                },
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
    agente = AgenteTriagemIncidentes(nome="Agente de Triagem de Incidentes")
    agente.run()