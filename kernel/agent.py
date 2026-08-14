from abc import ABC, abstractmethod
import psycopg2


class Agent(ABC):
    """
    Contrato comum que todo agente do kernel precisa seguir.
    Qualquer agente novo (Triagem de Incidentes, Backup, etc.)
    herda dessa classe e implementa os 3 métodos abaixo.
    """

    def __init__(self, nome: str):
        self.nome = nome

    @abstractmethod
    def perceive(self) -> dict:
        """Coleta o contexto/dado bruto que esse agente precisa observar."""
        raise NotImplementedError

    @abstractmethod
    def plan(self, contexto: dict) -> dict:
        """Manda o contexto pra IA e recebe de volta uma decisão/sugestão."""
        raise NotImplementedError

    @abstractmethod
    def act(self, plano: dict) -> None:
        """Executa (ou, no nosso caso, registra pra aprovação) o que foi decidido."""
        raise NotImplementedError

    def run(self) -> None:
        """Roda o ciclo completo: perceber -> planejar -> agir."""
        contexto = self.perceive()
        plano = self.plan(contexto)
        self.act(plano)

    def registrar_sugestao(self, texto: str) -> None:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="demo",
            password="demo123",
            dbname="smb_demo",
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sugestoes_pendentes (agente, sugestao) VALUES (%s, %s);",
            (self.nome, texto),
        )
        conn.commit()
        cur.close()
        conn.close()