"""Linha de comando.

python -m visao rastrear --cor vermelho --camera 0
python -m visao rastrear --cor azul --video entrada.mp4 --saida resultado.mp4
python -m visao linha --camera 0
python -m visao demo            # gera os GIFs de demonstração em docs/
"""

import argparse
import sys
from pathlib import Path

import cv2

from visao import cores, linha


def _abrir(args) -> cv2.VideoCapture:
    fonte = args.video if args.video else args.camera
    captura = cv2.VideoCapture(fonte)
    if not captura.isOpened():
        sys.exit(f"Não foi possível abrir {fonte!r}.")
    return captura


def _processar(args, processa_quadro) -> None:
    captura = _abrir(args)
    gravador = None
    try:
        while True:
            ok, quadro = captura.read()
            if not ok:
                break
            saida = processa_quadro(quadro)

            if args.saida:
                if gravador is None:
                    altura, largura = saida.shape[:2]
                    fps = captura.get(cv2.CAP_PROP_FPS) or 30
                    gravador = cv2.VideoWriter(
                        args.saida, cv2.VideoWriter_fourcc(*"mp4v"), fps, (largura, altura)
                    )
                gravador.write(saida)
            if not args.sem_janela:
                cv2.imshow("visao (q para sair)", saida)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        captura.release()
        if gravador is not None:
            gravador.release()
        cv2.destroyAllWindows()


def comando_rastrear(args) -> None:
    rastreador = cores.Rastreador(args.cor)
    _processar(args, lambda quadro: rastreador.desenhar(quadro, rastreador.atualizar(quadro)))


def comando_linha(args) -> None:
    def processa(quadro):
        leitura = linha.ler_linha(quadro)
        if args.mostrar_erro:
            print(leitura.erro)
        return linha.desenhar(quadro, leitura)

    _processar(args, processa)


def comando_demo(args) -> None:
    from visao.demo import gerar_demos

    for caminho in gerar_demos(Path(args.pasta)):
        print(f"gerado: {caminho}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m visao", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="comando", required=True)

    def entrada(p):
        grupo = p.add_mutually_exclusive_group()
        grupo.add_argument("--camera", type=int, default=0, help="índice da webcam (padrão 0)")
        grupo.add_argument("--video", help="arquivo de vídeo de entrada")
        p.add_argument("--saida", help="grava o resultado em um .mp4")
        p.add_argument("--sem-janela", action="store_true", help="não abre janela (útil em servidores)")

    rastrear = sub.add_parser("rastrear", help="rastreia um objeto pela cor")
    rastrear.add_argument("--cor", choices=sorted(cores.CORES), default="vermelho")
    entrada(rastrear)
    rastrear.set_defaults(func=comando_rastrear)

    seguir = sub.add_parser("linha", help="lê a posição da linha para um robô seguidor")
    seguir.add_argument("--mostrar-erro", action="store_true", help="imprime o erro de cada quadro")
    entrada(seguir)
    seguir.set_defaults(func=comando_linha)

    demo = sub.add_parser("demo", help="gera os GIFs de demonstração")
    demo.add_argument("--pasta", default="docs")
    demo.set_defaults(func=comando_demo)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
