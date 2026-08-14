import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="demo",
    password="demo123",
    dbname="smb_demo",
)
cur = conn.cursor()

cur.execute(
    "SELECT id, criado_em, agente, sugestao "
    "FROM sugestoes_pendentes WHERE status = 'pendente' ORDER BY criado_em DESC;"
)
sugestoes = cur.fetchall()
cur.close()
conn.close()

if not sugestoes:
    print("Nenhuma sugestão pendente.")
else:
    for id_, criado_em, agente, sugestao in sugestoes:
        print("=" * 60)
        print(f"#{id_} | {agente} | {criado_em}")
        print("-" * 60)
        print(sugestao)
    print("=" * 60)
    print(f"Total: {len(sugestoes)} sugestão(ões) pendente(s).")