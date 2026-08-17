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

cur.execute(
    "SELECT id, criado_em, agente, causa_provavel, confianca, proxima_acao "
    "FROM sugestoes_pendentes WHERE status = 'pendente' ORDER BY criado_em DESC;"
)
sugestoes = cur.fetchall()

if not sugestoes:
    print("Nenhuma sugestão pendente.")
else:
    for id_, criado_em, agente, causa_provavel, confianca, proxima_acao in sugestoes:
        print("=" * 60)
        print(f"#{id_} | {agente} | {criado_em}")
        print("-" * 60)
        print(f"Causa provável: {causa_provavel}")
        print(f"Confiança: {confianca}")
        print(f"Próxima ação: {proxima_acao}")
    print("=" * 60)
    print(f"Total: {len(sugestoes)} sugestão(ões) pendente(s).")

    escolha = input("\nDigite o número da sugestão pra revisar (ou Enter pra sair): ")

    if escolha.strip():
        id_escolhido = int(escolha)
        decisao = input("Aprovar (a) ou rejeitar (r)? ").strip().lower()
        novo_status = "aprovado" if decisao == "a" else "rejeitado"

        cur.execute(
            "UPDATE sugestoes_pendentes SET status = %s WHERE id = %s;",
            (novo_status, id_escolhido),
        )
        conn.commit()
        print(f"Sugestão #{id_escolhido} marcada como '{novo_status}'.")

cur.close()
conn.close()