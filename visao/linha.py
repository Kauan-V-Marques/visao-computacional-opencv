"""Detecção de linha para robô seguidor de linha usando a câmera.

A parte de baixo da imagem é dividida em faixas horizontais. Em cada faixa,
o centro da linha escura vira um ponto; com os pontos calculamos:
  * erro: deslocamento da linha em relação ao centro, de -1 (esquerda) a +1 (direita)
  * ângulo: inclinação da linha (curva à frente), em graus
O erro é exatamente a entrada que o controle PID do robô precisa.
"""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class LeituraLinha:
    pontos: list[tuple[int, int]]  # centro da linha em cada faixa (de baixo para cima)
    erro: float | None  # -1 a +1; None quando a linha não aparece
    angulo: float | None  # graus; positivo = curva para a direita

    @property
    def encontrou(self) -> bool:
        return self.erro is not None


def binarizar(frame_bgr: np.ndarray, contraste_minimo: float = 50.0) -> np.ndarray:
    """Linha escura em fundo claro vira branco (255). O limiar de Otsu se adapta à iluminação.

    O Otsu sempre divide a imagem em duas classes, mesmo sem linha nenhuma (ele separaria,
    por exemplo, o lado mais escuro de uma sombra). Por isso só aceitamos a divisão quando
    a "linha" é bem mais escura que o fundo.
    """
    cinza = cv2.GaussianBlur(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    limiar, binaria = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    escuros, claros = cinza[cinza <= limiar], cinza[cinza > limiar]
    if escuros.size == 0 or claros.size == 0 or claros.mean() - escuros.mean() < contraste_minimo:
        return np.zeros_like(binaria)
    return binaria


def ler_linha(
    frame_bgr: np.ndarray,
    faixas: int = 5,
    regiao: float = 0.5,
    pixels_minimos: int = 40,
    largura_maxima: float = 0.5,
) -> LeituraLinha:
    """Analisa a parte de baixo da imagem (fração `regiao` da altura) dividida em `faixas`."""
    altura, largura = frame_bgr.shape[:2]
    binaria = binarizar(frame_bgr)
    topo = int(altura * (1 - regiao))
    altura_faixa = (altura - topo) // faixas

    pontos: list[tuple[int, int]] = []
    for i in range(faixas):
        y2 = altura - i * altura_faixa
        y1 = y2 - altura_faixa
        faixa = binaria[y1:y2, :]
        pixels = cv2.countNonZero(faixa)
        # Pouca tinta = sem linha; tinta demais = sombra ou borda da pista, não a linha
        if pixels < pixels_minimos or pixels > faixa.size * largura_maxima:
            continue
        momentos = cv2.moments(faixa, binaryImage=True)
        x = int(momentos["m10"] / momentos["m00"])
        pontos.append((x, (y1 + y2) // 2))

    if not pontos:
        return LeituraLinha(pontos=[], erro=None, angulo=None)

    centro = largura / 2
    # A faixa mais próxima do robô (a de baixo) pesa mais no erro
    pesos = np.linspace(1.0, 0.4, len(pontos))
    x_medio = float(np.average([p[0] for p in pontos], weights=pesos))
    erro = float(np.clip((x_medio - centro) / centro, -1.0, 1.0))

    angulo = None
    if len(pontos) >= 2:
        (x_baixo, y_baixo), (x_cima, y_cima) = pontos[0], pontos[-1]
        angulo = float(np.degrees(np.arctan2(x_cima - x_baixo, y_baixo - y_cima)))

    return LeituraLinha(
        pontos=pontos, erro=round(erro, 3), angulo=None if angulo is None else round(angulo, 1)
    )


def desenhar(frame_bgr: np.ndarray, leitura: LeituraLinha) -> np.ndarray:
    saida = frame_bgr.copy()
    altura, largura = saida.shape[:2]
    cv2.line(saida, (largura // 2, altura // 2), (largura // 2, altura), (200, 200, 200), 1)

    for i in range(1, len(leitura.pontos)):
        cv2.line(saida, leitura.pontos[i - 1], leitura.pontos[i], (255, 120, 0), 3)
    for ponto in leitura.pontos:
        cv2.circle(saida, ponto, 6, (0, 0, 255), -1)

    if leitura.encontrou:
        # Barra de erro: verde perto do centro, vermelha nas pontas
        x_erro = int(largura / 2 + leitura.erro * largura / 2)
        cor = (0, int(255 * (1 - abs(leitura.erro))), int(255 * abs(leitura.erro)))
        cv2.rectangle(saida, (min(largura // 2, x_erro), 8), (max(largura // 2, x_erro), 20), cor, -1)
        texto = f"erro {leitura.erro:+.2f}"
        if leitura.angulo is not None:
            texto += f"  angulo {leitura.angulo:+.0f} graus"
        _legenda(saida, texto, (30, 30, 30))
    else:
        _legenda(saida, "linha perdida", (0, 0, 255))
    return saida


def _legenda(imagem: np.ndarray, texto: str, cor: tuple[int, int, int]) -> None:
    """Texto com fundo claro, legível mesmo quando passa por cima da linha."""
    (largura, altura), base = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
    cv2.rectangle(imagem, (6, 42 - altura - 6), (14 + largura, 42 + base + 2), (245, 245, 245), -1)
    cv2.putText(imagem, texto, (10, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.55, cor, 2)
