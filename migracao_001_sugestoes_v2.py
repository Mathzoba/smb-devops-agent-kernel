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
    cur.execute("ALTER TABLE sugestoes_pendentes ADD COLUMN IF NOT EXISTS evidencias JSONB;")
    cur.execute("ALTER TABLE sugestoes_pendentes ADD COLUMN IF NOT EXISTS evidencias_citadas TEXT;")
    cur.execute("ALTER TABLE sugestoes_pendentes ADD COLUMN IF NOT EXISTS motivo TEXT;")
    cur.execute("ALTER TABLE sugestoes_pendentes ADD COLUMN IF NOT EXISTS risco TEXT;")
    conn.commit()
    print("Migração 001 aplicada: colunas evidencias, evidencias_citadas, motivo e risco.")
finally:
    conn.close()