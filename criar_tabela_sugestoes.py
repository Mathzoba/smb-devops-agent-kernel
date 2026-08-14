import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="demo",
    password="demo123",
    dbname="smb_demo",
)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS sugestoes_pendentes (
        id SERIAL PRIMARY KEY,
        criado_em TIMESTAMP DEFAULT NOW(),
        agente TEXT NOT NULL,
        sugestao TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pendente'
    );
""")
conn.commit()

cur.close()
conn.close()
print("Tabela sugestoes_pendentes criada.")