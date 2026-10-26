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
    cur.execute("ALTER TABLE sugestoes_pendentes ADD COLUMN IF NOT EXISTS resultado TEXT;")
    cur.execute("ALTER TABLE sugestoes_pendentes ADD COLUMN IF NOT EXISTS lacunas JSONB;")
    conn.commit()
    print("Migração 002 aplicada: colunas resultado e lacunas.")
finally:
    conn.close()