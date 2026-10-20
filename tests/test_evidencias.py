from datetime import datetime
from agente_triagem_incidentes import alertas_para_evidencias


def test_alertas_viram_evidencias():
    # 1. Arrange: dois alertas falsos, no mesmo formato que a PostgresQueryTool devolve
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

    # 2. Act: chama a funcao
    evidencias = alertas_para_evidencias(linhas)

    # 3. Assert: confere o resultado
    assert len(evidencias) == 2
    assert evidencias[0].fonte == "postgres"
    assert evidencias[0].tipo == "alerta"
    assert evidencias[0].assunto == "api-pagamentos"
    assert evidencias[0].observacao == "[critico] Timeout ao conectar no banco de dados"