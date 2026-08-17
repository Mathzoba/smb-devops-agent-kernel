from abc import ABC, abstractmethod


class Tool(ABC):
    """
    Contrato comum para qualquer fonte de dados que um agente possa consultar.
    Tools sao sempre read-only: coletam informacao, nunca alteram nada.
    """

    def __init__(self, nome: str):
        self.nome = nome

    @abstractmethod
    def run(self, **kwargs) -> dict:
        """Executa a coleta e devolve um dicionario com o resultado."""
        raise NotImplementedError