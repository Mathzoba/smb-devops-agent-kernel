from kernel.schemas import Finding
from kernel.config import settings
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

    from kernel.schemas import Finding
# ... resto dos imports que já existem

    def registrar_sugestao(self, finding: Finding) -> None:
        conn = psycopg2.connect(
            host=settings.PG_HOST,
            port=settings.PG_PORT,
            user=settings.PG_USER,
            password=settings.PG_PASSWORD,
            dbname=settings.PG_DATABASE,
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sugestoes_pendentes (agente, causa_provavel, confianca, proxima_acao) "
            "VALUES (%s, %s, %s, %s);",
            (self.nome, finding.causa_provavel, finding.confianca, finding.proxima_acao),
        )
        conn.commit()
        cur.close()
        conn.close()