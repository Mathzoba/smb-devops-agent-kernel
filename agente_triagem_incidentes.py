from tool_prometheus_alertas import PrometheusAlertasTool
from dotenv import load_dotenv
from groq import Groq, APIError
from kernel.config import settings
from kernel.schemas import Evidence, Hypothesis, Recommendation, Abstention
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
                tipo="sem_monitoramento",
                fonte="prometheus",
                timestamp=coletado_em,
                assunto=servico,
                observacao="servico nao aparece entre os alvos monitorados pelo Prometheus",
            ))

    return evidencias

def evidencias_inexistentes(citadas: list[str], total: int) -> list[str]:
    """Devolve os ids citados que nao existem. Ex.: total=3 -> so E1, E2 e E3 sao validos."""
    validas = {f"E{numero}" for numero in range(1, total + 1)}
    return [citada for citada in citadas if citada not in validas]

def limitar_confianca(confianca: str, evidencias: list[Evidence]) -> str:
    """Regra: se algum servico alertado nao e monitorado, a confianca e no maximo 'baixa'."""
    if any(e.tipo == "sem_monitoramento" for e in evidencias):
        return "baixa"
    return confianca

def alertas_prometheus_para_evidencias(alertas: list[dict]) -> list[Evidence]:
    """Transforma alertas disparados do Prometheus em evidencias. Funcao pura."""
    evidencias = []
    for alerta in alertas:
        evidencias.append(Evidence(
            tipo="alerta",
            fonte="prometheus",
            timestamp=alerta["activeAt"],
            assunto=alerta["labels"]["job"],
            observacao=f"[{alerta['labels']['severidade']}] {alerta['annotations']['resumo']}",
        ))
    return evidencias

def montar_contexto(alertas: list[dict], alvos: list[dict], coletado_em: str) -> dict:
    """Recebe dados brutos (alertas e alvos) e monta as evidencias. Funcao pura."""
    servicos_alertados = [alerta["labels"]["job"] for alerta in alertas]
    evidencias = alertas_prometheus_para_evidencias(alertas)
    evidencias += alvos_para_evidencias(alvos, servicos_alertados, coletado_em)
    return {"evidencias": evidencias, "tem_incidente": len(alertas) > 0}


# ---------- Agente ----------

class AgenteTriagemIncidentes(Agent):
    def perceive(self) -> dict:
        # Coleta (Tools, somente leitura). A montagem das evidencias fica na funcao pura.
        alertas = PrometheusAlertasTool().run()["alertas"]
        alvos = PrometheusUpTool().run()["alvos"]
        return montar_contexto(alertas, alvos, str(datetime.now()))
    
    def plan(self, contexto: dict) -> dict:
        # Sem alerta disparado: nada a investigar, nao gasta LLM
        if not contexto["tem_incidente"]:
            return {"sem_incidente": True}

        evidencias = contexto["evidencias"]
        texto_evidencias = "\n".join(
            f"E{numero}: [{e.fonte}/{e.tipo}] {e.assunto}: {e.observacao} (em {e.timestamp})"
            for numero, e in enumerate(evidencias, start=1)
        )

        # Ate 2 tentativas: falha do LLM costuma ser passageira
        resposta = None
        for tentativa in range(1, 3):
            try:
                resposta = self._analisar(texto_evidencias)
                break
            except (APIError, json.JSONDecodeError, KeyError, TypeError) as falha:
                print(f"Tentativa {tentativa} falhou: {type(falha).__name__}")

        if resposta is None:
            return {"falha_analise": True, "evidencias": evidencias}

        hipotese, recomendacao, lacunas = resposta

        confianca_do_llm = hipotese.confianca
        hipotese.confianca = limitar_confianca(hipotese.confianca, evidencias)
        if hipotese.confianca != confianca_do_llm:
            print(f"Regra aplicada: confiança '{confianca_do_llm}' → '{hipotese.confianca}' (serviço sem monitoramento)")

        return {
            "evidencias": evidencias,
            "hipotese": hipotese,
            "recomendacao": recomendacao,
            "lacunas": lacunas,
        }

    def _analisar(self, texto_evidencias: str):
        """Pergunta ao LLM e monta as fichas. Pode levantar erro se a resposta vier com defeito."""
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
                        "Em 'lacunas', diga o que as evidências mostram, o que elas NÃO "
                        "permitem saber, e qual checagem traria a prova que falta. "
                        "Responda SOMENTE em JSON, exatamente neste formato: "
                        '{"hipotese": {"afirmacao": "...", "evidencias": ["E1"], '
                        '"confianca": "baixa|media|alta"}, '
                        '"recomendacao": {"acao": "...", "motivo": "...", '
                        '"risco": "baixo|medio|alto"}, '
                        '"lacunas": {"sabemos": "...", "nao_sabemos": "...", '
                        '"proxima_checagem": "..."}}'
                    ),
                },
                {"role": "user", "content": f"Evidências:\n{texto_evidencias}"},
            ],
        )
        dados = json.loads(resposta.choices[0].message.content)
        return (
            Hypothesis(**dados["hipotese"]),
            Recommendation(**dados["recomendacao"]),
            Abstention(**dados["lacunas"]),
        )

    def act(self, plano: dict) -> None:
        if plano.get("sem_incidente"):
            print("✅ Nenhum incidente ativo. Nenhum alerta disparado no Prometheus.")
            return
        if plano.get("falha_analise"):
            print("⚠️ FALHA AO ANALISAR: o LLM não devolveu resposta válida após 2 tentativas.")
            print("Evidências coletadas (fatos, sem análise):")
            for numero, e in enumerate(plano["evidencias"], start=1):
                print(f"  E{numero}: [{e.fonte}] {e.assunto}: {e.observacao}")
            return
        evidencias = plano["evidencias"]
        hipotese = plano["hipotese"]
        recomendacao = plano["recomendacao"]
        lacunas = plano["lacunas"]

        # Regra: confianca baixa = o agente se abstem de concluir
        abster = hipotese.confianca == "baixa"

        print("=" * 50)
        print(f"[{self.nome}] SUGESTÃO PENDENTE DE APROVAÇÃO HUMANA:")

        if abster:
            print("⚪ EVIDÊNCIA INSUFICIENTE — o agente não tem provas para concluir.")
            print(f"O que sabemos: {lacunas.sabemos}")
            print(f"O que NÃO sabemos: {lacunas.nao_sabemos}")
            print(f"Próxima checagem: {lacunas.proxima_checagem}")
            print(f"Hipótese (não confirmada): {hipotese.afirmacao}")
        else:
            print(f"Hipótese: {hipotese.afirmacao}")
            print(f"Ação recomendada: {recomendacao.acao}")
            print(f"Motivo: {recomendacao.motivo}")
            print(f"Risco: {recomendacao.risco}")

        print(f"Baseada em: {', '.join(hipotese.evidencias)}")
        inventadas = evidencias_inexistentes(hipotese.evidencias, len(evidencias))
        if inventadas:
            print(f"⚠️ ATENÇÃO: o agente citou evidências que não existem: {', '.join(inventadas)}")
        print(f"Confiança: {hipotese.confianca}")
        print("=" * 50)

        resultado = "evidencia_insuficiente" if abster else "conclusao"
        self.registrar_investigacao(evidencias, hipotese, recomendacao, lacunas, resultado)

if __name__ == "__main__":
    agente = AgenteTriagemIncidentes(nome="Agente de Triagem de Incidentes")
    agente.run()