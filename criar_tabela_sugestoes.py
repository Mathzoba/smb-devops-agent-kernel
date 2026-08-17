import psycopg2
from kernel.config import settings

conn = psycopg2.connect(
    host=settings.PG_HOST,
    port=settings.PG_PORT,
    user=settings.PG_USER,
    password=settings.PG_PASSWORD,
    dbname=settings.PG_DATABASE,
)
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS sugestoes_pendentes;")
cur.execute(
    """
    CREATE TABLE sugestoes_pendentes (
        id SERIAL PRIMARY KEY,
        criado_em TIMESTAMP DEFAULT NOW(),
        agente TEXT,
        causa_provavel TEXT,
        confianca TEXT,
        proxima_acao TEXT,
        status TEXT DEFAULT 'pendente'
    );
    """
)
conn.commit()
cur.close()
conn.close()
print("Tabela sugestoes_pendentes recriada com schema estruturado.")