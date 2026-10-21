import psycopg2
from kernel.config import settings


def evidencias_citadas_por_extenso(evidencias: list, citadas: str) -> list[str]:
    """Pega 'E1, E4' e devolve o texto da E1 e da E4. Funcao pura."""
    linhas = []
    for id_ in citadas.split(", "):
        numero = int(id_[1:])                 # "E4" -> 4
        if 1 <= numero <= len(evidencias):
            e = evidencias[numero - 1]        # E1 fica na posicao 0 da lista
            linhas.append(f"  {id_}: [{e['fonte']}] {e['assunto']}: {e['observacao']}")
        else:
            linhas.append(f"  {id_}: ⚠️ evidência não existe")
    return linhas


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
        "SELECT id, criado_em, agente, causa_provavel, confianca, proxima_acao, "
        "motivo, risco, evidencias, evidencias_citadas "
        "FROM sugestoes_pendentes WHERE status = 'pendente' ORDER BY criado_em DESC;"
    )
    sugestoes = cur.fetchall()

    if not sugestoes:
        print("Nenhuma sugestão pendente.")
    else:
        for (id_, criado_em, agente, causa, confianca, acao,
             motivo, risco, evidencias, citadas) in sugestoes:
            print("=" * 60)
            print(f"#{id_} | {agente} | {criado_em}")
            print("-" * 60)
            print(f"Hipótese: {causa}")
            print(f"Confiança: {confianca}")
            print(f"Ação: {acao}")
            if motivo:
                print(f"Motivo: {motivo}")
                print(f"Risco: {risco}")
            if evidencias and citadas:
                print(f"Baseada em ({citadas}):")
                for linha in evidencias_citadas_por_extenso(evidencias, citadas):
                    print(linha)
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
finally:
    conn.close()