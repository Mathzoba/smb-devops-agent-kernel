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
    CREATE TABLE IF NOT EXISTS backups (
        id SERIAL PRIMARY KEY,
        criado_em TIMESTAMP DEFAULT NOW(),
        servico TEXT NOT NULL, 
        status TEXT NOT NULL,
        detalhe TEXT NOT NULL
    ); 
""")
conn.commit()

cur.execute(
    "INSERT INTO backups (servico, status, detalhe) VALUES (%s, %s, %s)",
    ("banco-clientes", "concluido", "Backup finalizado em 3min, 450MB")
)

conn.commit()

cur.execute(
    "INSERT INTO backups (servico, status, detalhe) VALUES (%s, %s, %s);",
    ("arquivos-financeiro", "falhou", "Sem espaco em disco")
)
conn.commit()

cur.execute("SELECT id, criado_em, servico, status, detalhe FROM backups;")
for linha in cur.fetchall():
    print(linha)

cur.close()
conn.close()
