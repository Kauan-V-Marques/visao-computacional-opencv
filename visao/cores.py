"""Detecção e rastreamento de objetos por cor (segmentação no espaço HSV)."""

from collections import deque
from dataclasses import dataclass

import cv2
import numpy as np

# Faixas HSV do OpenCV: H de 0 a 179, S e V de 0 a 255.
# O vermelho fica nas duas pontas do círculo de matiz, por isso tem duas faixas.
CORES: dict[str, list[tuple[tuple[int, int, int], tuple[int, int, int]]]] = {
    "vermelho": [((0, 120, 70), (10, 255, 255)), ((170, 120, 70), (179, 255, 255))],
    "laranja": [((11, 120, 90), (24, 255, 255))],
    "amarelo": [((25, 100, 100), (35, 255, 255))],
    "verde": [((40, 70, 60), (85, 255, 255))],
    "azul": [((95, 120, 60), (130, 255, 255))],
}


@dataclass(frozen=True)
class Deteccao:
    centro: tuple[int, int]
    raio: int
    area: float
    caixa: tuple[int, int, int, int]  # x, y, largura, altura


def mascara_da_cor(frame_bgr: np.ndarray, cor: str) -> np.ndarray:
    """Máscara binária (0/255) dos pixels da cor, já sem ruído."""
    if cor not in CORES:
        raise ValueError(f"Cor desconhecida: {cor}. Opções: {', '.join(CORES)}")

    # Desfoque antes da conversão reduz ruído do sensor da câmera
    hsv = cv2.cvtColor(cv2.GaussianBlur(frame_bgr, (5, 5), 0), cv2.COLOR_BGR2HSV)
    mascara = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for baixo, alto in CORES[cor]:
        mascara |= cv2.inRange(hsv, np.array(baixo), np.array(alto))

    # Abertura remove pontinhos isolados; fechamento tapa buracos dentro do objeto
    nucleo = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, nucleo, iterations=2)
    return cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, nucleo, iterations=2)


def detectar(frame_bgr: np.ndarray, cor: str, area_minima: float = 150.0) -> Deteccao | None:
    """Maior objeto da cor no quadro, ou None se não houver nada grande o bastante."""
    contornos, _ = cv2.findContours(
        mascara_da_cor(frame_bgr, cor), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contornos:
        return None

    maior = max(contornos, key=cv2.contourArea)
    area = cv2.contourArea(maior)
    if area < area_minima:
        return None

    momentos = cv2.moments(maior)
    centro = (int(momentos["m10"] / momentos["m00"]), int(momentos["m01"] / momentos["m00"]))
    _, raio = cv2.minEnclosingCircle(maior)
    return Deteccao(centro=centro, raio=int(raio), area=area, caixa=cv2.boundingRect(maior))


class Rastreador:
    """Acompanha o objeto quadro a quadro e guarda o rastro das últimas posições."""

    def __init__(self, cor: str, tamanho_rastro: int = 32):
        self.cor = cor
        self.rastro: deque[tuple[int, int]] = deque(maxlen=tamanho_rastro)

    def atualizar(self, frame_bgr: np.ndarray) -> Deteccao | None:
        deteccao = detectar(frame_bgr, self.cor)
        if deteccao is not None:
            self.rastro.appendleft(deteccao.centro)
        return deteccao

    def desenhar(self, frame_bgr: np.ndarray, deteccao: Deteccao | None) -> np.ndarray:
        saida = frame_bgr.copy()
        pontos = list(self.rastro)
        for i in range(1, len(pontos)):
            espessura = max(1, int(6 * (1 - i / len(pontos))))
            cv2.line(saida, pontos[i - 1], pontos[i], (0, 255, 255), espessura)

        if deteccao is not None:
            x, y, w, h = deteccao.caixa
            cv2.rectangle(saida, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(saida, deteccao.centro, 4, (0, 0, 255), -1)
            texto = f"{self.cor} ({deteccao.centro[0]}, {deteccao.centro[1]})"
            cv2.putText(saida, texto, (x, max(15, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        else:
            cv2.putText(
                saida, "objeto nao encontrado", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2
            )
        return saida
