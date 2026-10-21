from datetime import datetime
from agente_triagem_incidentes import (
    alertas_para_evidencias,
    alvos_para_evidencias,
    evidencias_inexistentes,
)


def test_alertas_viram_evidencias():
    linhas = [
        {
            "id": 1,
            "criado_em": datetime(2026, 10, 20, 14, 0, 0),
            "servico": "api-pagamentos",
            "severidade": "critico",
            "mensagem": "Timeout ao conectar no banco de dados",
        },
        {
            "id": 2,
            "criado_em": datetime(2026, 10, 20, 14, 5, 0),
            "servico": "api-estoque",
            "severidade": "alto",
            "mensagem": "Latencia acima de 2s",
        },
    ]

    evidencias = alertas_para_evidencias(linhas)

    assert len(evidencias) == 2
    assert evidencias[0].fonte == "postgres"
    assert evidencias[0].tipo == "alerta"
    assert evidencias[0].assunto == "api-pagamentos"
    assert evidencias[0].observacao == "[critico] Timeout ao conectar no banco de dados"


def test_servico_sem_monitoramento_vira_evidencia():
    alvos = [{"job": "prometheus", "instance": "localhost:9090", "status": "ativo"}]

    evidencias = alvos_para_evidencias(alvos, ["api-pagamentos"], "2026-10-20 14:00:00")

    assert len(evidencias) == 2
    assert evidencias[1].assunto == "api-pagamentos"
    assert "nao aparece" in evidencias[1].observacao


def test_servico_monitorado_nao_gera_alerta_de_monitoramento():
    alvos = [{"job": "api-pagamentos", "instance": "api:8080", "status": "ativo"}]

    evidencias = alvos_para_evidencias(alvos, ["api-pagamentos"], "2026-10-20 14:00:00")

    assert len(evidencias) == 1

def test_detecta_evidencia_inventada():
    assert evidencias_inexistentes(["E1", "E9"], total=3) == ["E9"]


def test_todas_evidencias_validas():
    assert evidencias_inexistentes(["E1", "E3"], total=3) == []