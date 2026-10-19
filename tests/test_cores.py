import math

import pytest

from visao import cores, sintetico


def distancia(a, b):
    return math.dist(a, b)


@pytest.mark.parametrize("cor", ["vermelho", "laranja", "amarelo", "verde", "azul"])
def test_encontra_a_bola_de_cada_cor_na_posicao_certa(cor):
    centro = (150, 220)
    quadro = sintetico.quadro_com_bola(centro, cor=cor, distrator="azul" if cor != "azul" else "verde")

    deteccao = cores.detectar(quadro, cor)

    assert deteccao is not None
    assert distancia(deteccao.centro, centro) <= 2
    assert abs(deteccao.raio - 22) <= 3


def test_ignora_objeto_de_outra_cor():
    quadro = sintetico.quadro_com_bola((240, 180), cor="verde", distrator="azul")

    assert cores.detectar(quadro, "vermelho") is None


def test_vermelho_usa_as_duas_pontas_do_circulo_de_matiz():
    # Matiz ~175 (vermelho "puxado para o rosa") cai na segunda faixa
    quadro = sintetico.fundo()
    import cv2

    cv2.circle(quadro, (200, 150), 25, (70, 20, 200), -1)

    deteccao = cores.detectar(quadro, "vermelho")

    assert deteccao is not None
    assert distancia(deteccao.centro, (200, 150)) <= 2


def test_objeto_pequeno_demais_e_tratado_como_ruido():
    quadro = sintetico.quadro_com_bola((240, 180), raio=5, distrator=None)

    assert cores.detectar(quadro, "vermelho") is None


def test_cor_desconhecida_gera_erro_claro():
    with pytest.raises(ValueError, match="Cor desconhecida"):
        cores.mascara_da_cor(sintetico.fundo(), "roxo")


def test_rastreador_segue_a_trajetoria_e_guarda_o_rastro():
    rastreador = cores.Rastreador("vermelho", tamanho_rastro=10)
    trajetoria = sintetico.trajetoria_bola(30)

    for i, centro in enumerate(trajetoria):
        deteccao = rastreador.atualizar(sintetico.quadro_com_bola(centro, semente=i))
        assert deteccao is not None
        assert distancia(deteccao.centro, centro) <= 3

    assert len(rastreador.rastro) == 10
    assert distancia(rastreador.rastro[0], trajetoria[-1]) <= 3


def test_desenho_nao_altera_o_quadro_original():
    quadro = sintetico.quadro_com_bola((100, 100))
    copia = quadro.copy()
    rastreador = cores.Rastreador("vermelho")

    rastreador.desenhar(quadro, rastreador.atualizar(quadro))

    assert (quadro == copia).all()
