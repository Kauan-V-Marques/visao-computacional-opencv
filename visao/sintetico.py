"""Gera quadros sintéticos com resposta conhecida, usados nos testes e nas demonstrações."""

import math

import cv2
import numpy as np

CORES_BGR = {
    "vermelho": (40, 40, 220),
    "laranja": (30, 140, 245),
    "amarelo": (40, 220, 235),
    "verde": (60, 180, 60),
    "azul": (220, 110, 30),
}


def fundo(largura: int = 480, altura: int = 360, semente: int = 0) -> np.ndarray:
    """Fundo cinza com degradê e ruído, imitando a imagem de uma câmera simples."""
    rng = np.random.default_rng(semente)
    gradiente = np.linspace(150, 200, largura, dtype=np.float32)[None, :, None]
    imagem = np.repeat(np.repeat(gradiente, altura, axis=0), 3, axis=2)
    imagem += rng.normal(0, 6, imagem.shape)
    return np.clip(imagem, 0, 255).astype(np.uint8)


def quadro_com_bola(
    centro: tuple[int, int],
    cor: str = "vermelho",
    raio: int = 22,
    distrator: str | None = "azul",
    semente: int = 0,
) -> np.ndarray:
    imagem = fundo(semente=semente)
    if distrator:
        cv2.rectangle(imagem, (380, 40), (440, 90), CORES_BGR[distrator], -1)
    cv2.circle(imagem, centro, raio, CORES_BGR[cor], -1, lineType=cv2.LINE_AA)
    return imagem


def trajetoria_bola(quadros: int = 60) -> list[tuple[int, int]]:
    """Bola percorrendo uma lemniscata (um "oito deitado")."""
    pontos = []
    for i in range(quadros):
        t = 2 * math.pi * i / quadros
        escala = 1 + math.sin(t) ** 2
        pontos.append(
            (int(240 + 160 * math.cos(t) / escala), int(180 + 110 * math.sin(t) * math.cos(t) / escala))
        )
    return pontos


def quadro_com_linha(
    deslocamento: float = 0.0,
    curvatura: float = 0.0,
    largura_linha: int = 28,
    semente: int = 0,
    lacuna: tuple[int, int] | None = None,
) -> np.ndarray:
    """Pista vista pela câmera do robô.

    deslocamento: posição da linha na base da imagem, de -1 (esquerda) a +1 (direita).
    curvatura: quanto a linha se desloca até o topo (negativo = curva para a esquerda).
    lacuna: faixa de linhas (y1, y2) sem tinta, simulando um trecho apagado.
    """
    largura, altura = 480, 360
    imagem = clarear(fundo(largura, altura, semente), 40)
    centro = largura / 2
    pontos = []
    for y in range(altura, -1, -6):
        progresso = (altura - y) / altura
        x = centro + deslocamento * centro + curvatura * centro * progresso**2
        pontos.append((int(x), y))
    cv2.polylines(imagem, [np.array(pontos, dtype=np.int32)], False, (25, 25, 25), largura_linha, cv2.LINE_AA)
    if lacuna:
        limpo = clarear(fundo(largura, altura, semente + 1), 40)
        imagem[lacuna[0] : lacuna[1], :] = limpo[lacuna[0] : lacuna[1], :]
    return imagem


def clarear(imagem: np.ndarray, valor: int) -> np.ndarray:
    """Soma com saturação: em uint8, 250 + 40 daria 34; aqui fica 255."""
    return cv2.add(imagem, np.full_like(imagem, valor))
