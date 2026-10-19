"""Gera os GIFs do README a partir de quadros sintéticos (resultado reproduzível)."""

import math
from pathlib import Path

import cv2
from PIL import Image

from visao import cores, linha, sintetico


def _salvar_gif(quadros_bgr, caminho: Path, ms_por_quadro: int = 50) -> Path:
    imagens = [
        Image.fromarray(cv2.cvtColor(q, cv2.COLOR_BGR2RGB)).resize((360, 270), Image.Resampling.BILINEAR)
        for q in quadros_bgr
    ]
    # Uma paleta só para todos os quadros e sem pontilhado: o que não muda entre quadros
    # fica idêntico e o GIF comprime muito melhor
    amostras = imagens[:: max(1, len(imagens) // 8)]
    mosaico = Image.new("RGB", (360 * len(amostras), 270 + 60))
    for i, amostra in enumerate(amostras):
        mosaico.paste(amostra, (360 * i, 0))
    # Faixa com o degradê verde -> vermelho da barra de erro, para essas cores entrarem na paleta
    for passo in range(12):
        nivel = passo / 11
        cor = (int(255 * nivel), int(255 * (1 - nivel)), 0)
        largura = mosaico.width // 12
        mosaico.paste(cor, (passo * largura, 270, (passo + 1) * largura, 330))
    paleta = mosaico.quantize(colors=96, dither=Image.Dither.NONE)
    convertidas = [img.quantize(palette=paleta, dither=Image.Dither.NONE) for img in imagens]
    convertidas[0].save(
        caminho, save_all=True, append_images=convertidas[1:], duration=ms_por_quadro, loop=0, optimize=True
    )
    return caminho


def gerar_demos(pasta: Path) -> list[Path]:
    pasta.mkdir(parents=True, exist_ok=True)

    rastreador = cores.Rastreador("vermelho")
    quadros = []
    for centro in sintetico.trajetoria_bola(60):
        quadro = sintetico.quadro_com_bola(centro)
        quadros.append(rastreador.desenhar(quadro, rastreador.atualizar(quadro)))
    gif_cor = _salvar_gif(quadros, pasta / "rastreamento-cor.gif")

    quadros = []
    for i in range(60):
        t = 2 * math.pi * i / 60
        quadro = sintetico.quadro_com_linha(deslocamento=0.35 * math.sin(t), curvatura=0.5 * math.cos(t))
        quadros.append(linha.desenhar(quadro, linha.ler_linha(quadro)))
    gif_linha = _salvar_gif(quadros, pasta / "seguidor-de-linha.gif", ms_por_quadro=70)

    return [gif_cor, gif_linha]
