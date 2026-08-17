import psycopg2
from kernel.config import settings
from kernel.tools import Tool


class PostgresQueryTool(Tool):
    """
    Tool generica: roda um SELECT e devolve as linhas como lista de dicts.
    Reutilizavel por qualquer agente que le de uma tabela do Postgres.
    """

    def __init__(self):
        super().__init__(nome="postgres_query")

    def run(self, query: str) -> dict:
        conn = psycopg2.connect(
            host=settings.PG_HOST,
            port=settings.PG_PORT,
            user=settings.PG_USER,
            password=settings.PG_PASSWORD,
            dbname=settings.PG_DATABASE,
        )
        cur = conn.cursor()
        cur.execute(query)
        colunas = [desc[0] for desc in cur.description]
        linhas = cur.fetchall()
        cur.close()
        conn.close()
        resultado = [dict(zip(colunas, linha)) for linha in linhas]
        return {"linhas": resultado}