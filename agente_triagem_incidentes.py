from tool_postgres_query import PostgresQueryTool
from dotenv import load_dotenv
from groq import Groq
from kernel.config import settings
from kernel.schemas import Finding, Evidence, Hypothesis, Recommendation
from kernel.agent import Agent
import json
from tool_prometheus_query import PrometheusUpTool
from datetime import datetime

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
        # 1. Coleta (Tools, precisam de banco/rede)
        dados_alertas = PostgresQueryTool().run(
            query=(
                "SELECT id, criado_em, servico, severidade, mensagem "
                "FROM alertas ORDER BY criado_em DESC LIMIT 10;"
            )
        )
        dados_prometheus = PrometheusUpTool().run()

        # 2. Transformacao em evidencia (funcoes puras, testadas)
        linhas = dados_alertas["linhas"]
        servicos_alertados = [alerta["servico"] for alerta in linhas]
        coletado_em = str(datetime.now())

        evidencias = alertas_para_evidencias(linhas)
        evidencias += alvos_para_evidencias(
            dados_prometheus["alvos"], servicos_alertados, coletado_em
        )
        return {"evidencias": evidencias}
    
    def plan(self, contexto: dict) -> dict:
        evidencias = contexto["evidencias"]

        # Numera as evidencias: E1, E2, E3...
        texto_evidencias = "\n".join(
            f"E{numero}: [{e.fonte}/{e.tipo}] {e.assunto}: {e.observacao} (em {e.timestamp})"
            for numero, e in enumerate(evidencias, start=1)
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
                        "Você recebe evidências numeradas (E1, E2...) coletadas por ferramentas. "
                        "Baseie sua análise SOMENTE nessas evidências; não invente fatos. "
                        "Na hipótese, cite os números das evidências que a sustentam. "
                        "Falta de monitoramento é falta de evidência, não é a causa do problema. "
                        "Na recomendação, informe o risco de executar a ação. "
                        "Responda SOMENTE em JSON, exatamente neste formato: "
                        '{"hipotese": {"afirmacao": "...", "evidencias": ["E1"], '
                        '"confianca": "baixa|media|alta"}, '
                        '"recomendacao": {"acao": "...", "motivo": "...", '
                        '"risco": "baixo|medio|alto"}}'
                    ),
                },
                {
                    "role": "user",
                    "content": f"Evidências:\n{texto_evidencias}",
                },
            ],
        )
        dados = json.loads(resposta.choices[0].message.content)

        hipotese = Hypothesis(**dados["hipotese"])
        recomendacao = Recommendation(**dados["recomendacao"])
        return {"hipotese": hipotese, "recomendacao": recomendacao}

    def act(self, plano: dict) -> None:
        hipotese = plano["hipotese"]
        recomendacao = plano["recomendacao"]

        print("=" * 50)
        print(f"[{self.nome}] SUGESTÃO PENDENTE DE APROVAÇÃO HUMANA:")
        print(f"Hipótese: {hipotese.afirmacao}")
        print(f"Baseada em: {', '.join(hipotese.evidencias)}")
        print(f"Confiança: {hipotese.confianca}")
        print(f"Ação recomendada: {recomendacao.acao}")
        print(f"Motivo: {recomendacao.motivo}")
        print(f"Risco: {recomendacao.risco}")
        print("=" * 50)

        # Ponte temporaria: o banco ainda usa o formato antigo (Finding)
        self.registrar_sugestao(Finding(
            causa_provavel=hipotese.afirmacao,
            confianca=hipotese.confianca,
            proxima_acao=recomendacao.acao,
        ))


if __name__ == "__main__":
    agente = AgenteTriagemIncidentes(nome="Agente de Triagem de Incidentes")
    agente.run()