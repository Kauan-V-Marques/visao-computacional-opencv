import pytest

from visao import linha, sintetico


def test_linha_centralizada_tem_erro_perto_de_zero():
    leitura = linha.ler_linha(sintetico.quadro_com_linha(deslocamento=0.0))

    assert leitura.encontrou
    assert abs(leitura.erro) < 0.05
    assert abs(leitura.angulo) < 5


@pytest.mark.parametrize("deslocamento", [-0.6, -0.3, 0.3, 0.6])
def test_erro_acompanha_o_lado_e_a_distancia_da_linha(deslocamento):
    leitura = linha.ler_linha(sintetico.quadro_com_linha(deslocamento=deslocamento))

    assert leitura.erro == pytest.approx(deslocamento, abs=0.08)


def test_erro_cresce_conforme_a_linha_se_afasta():
    erros = [linha.ler_linha(sintetico.quadro_com_linha(deslocamento=d)).erro for d in (0.1, 0.3, 0.5, 0.7)]

    assert erros == sorted(erros)


@pytest.mark.parametrize(("curvatura", "sinal"), [(0.8, 1), (-0.8, -1)])
def test_angulo_indica_o_lado_da_curva(curvatura, sinal):
    leitura = linha.ler_linha(sintetico.quadro_com_linha(curvatura=curvatura))

    assert leitura.angulo * sinal > 10


def test_sem_linha_retorna_linha_perdida():
    leitura = linha.ler_linha(sintetico.fundo())

    assert not leitura.encontrou
    assert leitura.pontos == []


def test_sombra_grande_nao_e_confundida_com_linha():
    quadro = sintetico.clarear(sintetico.fundo(), 40)
    quadro[:, :300] = (quadro[:, :300] * 0.3).astype(quadro.dtype)  # 60% da imagem na sombra

    assert not linha.ler_linha(quadro).encontrou


def test_trecho_apagado_ainda_e_lido_pelas_outras_faixas():
    quadro = sintetico.quadro_com_linha(deslocamento=0.4, lacuna=(250, 290))

    leitura = linha.ler_linha(quadro)

    assert leitura.encontrou
    assert len(leitura.pontos) < 5
    assert leitura.erro == pytest.approx(0.4, abs=0.08)


def test_funciona_com_ruido_diferente_em_cada_quadro():
    for semente in range(10):
        leitura = linha.ler_linha(sintetico.quadro_com_linha(deslocamento=-0.25, semente=semente))
        assert leitura.erro == pytest.approx(-0.25, abs=0.08)
