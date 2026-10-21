import pytest
import psycopg2
from tool_postgres_query import PostgresQueryTool


def test_postgres_tool_recusa_escrita():
    # DELETE que nao apaga nada (WHERE 1 = 0), mas continua sendo uma escrita.
    # Uma Tool read-only de verdade precisa ser recusada pelo proprio banco.
    with pytest.raises(psycopg2.errors.ReadOnlySqlTransaction):
        PostgresQueryTool().run(query="DELETE FROM alertas WHERE 1 = 0;")

def test_postgres_tool_cancela_consulta_lenta():
    # pg_sleep(10) = uma consulta que demora 10 segundos de propósito
    with pytest.raises(psycopg2.errors.QueryCanceled):
        PostgresQueryTool().run(query="SELECT pg_sleep(10);")