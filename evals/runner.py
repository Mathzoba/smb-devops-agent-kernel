import glob
import json

from agente_triagem_incidentes import AgenteTriagemIncidentes, montar_contexto

RODADAS = 5


def avaliar(plano: dict, gabarito: dict) -> list[str]:
    """Compara a resposta do agente com o gabarito. Devolve a lista de erros (vazia = passou)."""
    erros = []

    if gabarito.get("sem_incidente"):
        if not plano.get("sem_incidente"):
            erros.append("deveria dizer 'nenhum incidente', mas investigou")
        return erros

    if plano.get("sem_incidente"):
        return ["deveria investigar, mas disse 'nenhum incidente'"]

    if plano.get("falha_analise"):
        return ["falha ao analisar (LLM não respondeu válido em 2 tentativas)"]

    hipotese = plano["hipotese"]
    citadas = set(hipotese.evidencias)
    
    for e in gabarito.get("deve_citar", []):
        if e not in citadas:
            erros.append(f"não citou {e}")
    for e in gabarito.get("nao_deve_citar", []):
        if e in citadas:
            erros.append(f"citou {e}, que é irrelevante")
    for palavra in gabarito.get("proibido_na_hipotese", []):
        if palavra.lower() in hipotese.afirmacao.lower():
            erros.append(f"hipótese fala de '{palavra}' sem prova")
    if gabarito.get("deve_concluir") and hipotese.confianca == "baixa":
        erros.append("se absteve, mas havia prova suficiente")
    if gabarito.get("deve_abster") and hipotese.confianca != "baixa":
        erros.append("deveria se abster (sem prova), mas concluiu")

    return erros


def main():
    agente = AgenteTriagemIncidentes(nome="Eval")
    total_passou = 0
    total_rodadas = 0

    for arquivo in sorted(glob.glob("evals/casos/*.json")):
        with open(arquivo, encoding="utf-8") as f:
            caso = json.load(f)

        contexto = montar_contexto(caso["alertas"], caso["alvos"], "2026-01-01 00:00:00")

        print("=" * 60)
        print(f"Cenário: {caso['nome']}")
        passou = 0
        for rodada in range(1, RODADAS + 1):
            try:
                plano = agente.plan(contexto)
                erros = avaliar(plano, caso["gabarito"])
            except Exception as falha:
                erros = [f"falha técnica: {type(falha).__name__}"]
            if erros:
                print(f"  rodada {rodada}: ❌ " + "; ".join(erros))
            else:
                passou += 1
        print(f"  Nota: {passou}/{RODADAS}")

        total_passou += passou
        total_rodadas += RODADAS

    print("=" * 60)
    print(f"TOTAL: {total_passou}/{total_rodadas}")


if __name__ == "__main__":
    main()