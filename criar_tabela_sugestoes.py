import psycopg2
from kernel.config import settings

conn = psycopg2.connect(
    host=settings.PG_HOST,
    port=settings.PG_PORT,
    user=settings.PG_USER,
    password=settings.PG_PASSWORD,
    dbname=settings.PG_DATABASE,
)
try:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sugestoes_pendentes (
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
    print("Tabela sugestoes_pendentes pronta (criada se não existia).")
finally:
    conn.close()