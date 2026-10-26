from kernel.schemas import Finding, Evidence, Hypothesis, Recommendation, Abstention
from kernel.config import settings
from abc import ABC, abstractmethod
from dataclasses import asdict
import json
import psycopg2


def _conectar():
    """Abre conexao com escrita. Usada so pelo kernel para registrar resultados."""
    return psycopg2.connect(
        host=settings.PG_HOST,
        port=settings.PG_PORT,
        user=settings.PG_USER,
        password=settings.PG_PASSWORD,
        dbname=settings.PG_DATABASE,
    )


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

    def registrar_sugestao(self, finding: Finding) -> None:
        """Formato antigo (so 3 campos). Ainda usado pelos agentes de backup e infra."""
        conn = _conectar()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO sugestoes_pendentes (agente, causa_provavel, confianca, proxima_acao) "
                "VALUES (%s, %s, %s, %s);",
                (self.nome, finding.causa_provavel, finding.confianca, finding.proxima_acao),
            )
            conn.commit()
        finally:
            conn.close()

    def registrar_investigacao(
        self,
        evidencias: list[Evidence],
        hipotese: Hypothesis,
        recomendacao: Recommendation,
        lacunas: Abstention | None = None,
        resultado: str = "conclusao",
    ) -> None:
        """Salva evidencias, hipotese, recomendacao e, se houver, as lacunas."""
        evidencias_json = json.dumps([asdict(e) for e in evidencias], ensure_ascii=False)
        lacunas_json = json.dumps(asdict(lacunas), ensure_ascii=False) if lacunas else None
        conn = _conectar()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO sugestoes_pendentes "
                "(agente, causa_provavel, confianca, proxima_acao, "
                "evidencias, evidencias_citadas, motivo, risco, resultado, lacunas) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                (
                    self.nome,
                    hipotese.afirmacao,
                    hipotese.confianca,
                    recomendacao.acao,
                    evidencias_json,
                    ", ".join(hipotese.evidencias),
                    recomendacao.motivo,
                    recomendacao.risco,
                    resultado,
                    lacunas_json,
                ),
            )
            conn.commit()
        finally:
            conn.close()