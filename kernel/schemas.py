from dataclasses import dataclass


@dataclass
class Finding:
    """
    Resultado estruturado que um agente produz apos analisar um contexto.
    Substitui a sugestao em texto livre.
    """
    causa_provavel: str
    confianca: str  # "baixa", "media" ou "alta"
    proxima_acao: str

@dataclass
class Evidence:
    """
    Fato observado por uma Tool, produzido pelo codigo Python (nunca pelo LLM).
    Serve de base para a conclusao do agente.
    """
    tipo: str        # "alerta" ou "monitoramento"
    fonte: str       # "postgres" ou "prometheus"
    timestamp: str   # quando o fato aconteceu ou foi coletado
    assunto: str     # servico a que o fato se refere, ex.: "api-pagamentos"
    observacao: str  # o fato em si, curto e sem opiniao

@dataclass
class Hypothesis:
    """O que o agente acha que aconteceu, apontando as evidencias que sustentam."""
    afirmacao: str            # ex.: "Falha de conexao com o banco"
    evidencias: list[str]     # ids das evidencias citadas, ex.: ["E1", "E2"]
    confianca: str            # "baixa", "media" ou "alta"


@dataclass
class Recommendation:
    """O que fazer, por que, e qual o risco de fazer."""
    acao: str                 # ex.: "Verificar logs do PostgreSQL"
    motivo: str               # por que essa acao ajuda
    risco: str                # "baixo", "medio" ou "alto"