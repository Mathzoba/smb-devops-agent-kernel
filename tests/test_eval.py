from kernel.schemas import Hypothesis
from evals.runner import avaliar


def hipotese(confianca: str, citadas: list[str]) -> Hypothesis:
    return Hypothesis(afirmacao="api fora do ar", evidencias=citadas, confianca=confianca)


def test_avaliar_reprova_quando_nao_se_abstem():
    plano = {"hipotese": hipotese("alta", ["E1"])}
    erros = avaliar(plano, {"deve_abster": True})
    assert len(erros) == 1


def test_avaliar_aprova_quando_se_abstem():
    plano = {"hipotese": hipotese("baixa", ["E1"])}
    erros = avaliar(plano, {"deve_abster": True})
    assert erros == []