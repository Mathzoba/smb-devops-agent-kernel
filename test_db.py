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

cur.execute("""
    CREATE TABLE IF NOT EXISTS alertas (
        id SERIAL PRIMARY KEY,
        criado_em TIMESTAMP DEFAULT NOW(),
        servico TEXT NOT NULL,
        severidade TEXT NOT NULL,
        mensagem TEXT NOT NULL
    );
""")
conn.commit()

cur.execute(
    "INSERT INTO alertas (servico, severidade, mensagem) VALUES (%s, %s, %s);",
    ("api-pagamentos", "critico", "Timeout ao conectar no banco de dados"),
)
conn.commit()

cur.execute("SELECT id, criado_em, servico, severidade, mensagem FROM alertas;")
for linha in cur.fetchall():
    print(linha)

cur.close()
conn.close()