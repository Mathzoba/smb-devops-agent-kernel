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