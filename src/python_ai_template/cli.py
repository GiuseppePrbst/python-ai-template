"""Interfaz de linea de comandos del generador.

Expone :func:`main`, que se registra como console script
``new-python-project`` en ``pyproject.toml`` y se reexporta como
``python_ai_template.cli:main``. Implementa ``--version`` y ``--help``;
delega la generacion en :mod:`python_ai_template.generator`.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from python_ai_template import __version__
from python_ai_template.generator import generate


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="new-python-project",
        description=(
            "Genera un proyecto Python a partir de la plantilla python-ai-template."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--name", help="nombre visible del proyecto")
    parser.add_argument(
        "--package",
        help=(
            "nombre del paquete Python (identificador valido, no keyword, "
            "solo ASCII, sin puntos, guiones, espacios ni separadores de "
            "ruta)"
        ),
    )
    parser.add_argument(
        "--destination",
        help="ruta del directorio destino (no debe existir)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.name is None or args.package is None or args.destination is None:
        parser.print_usage(sys.stderr)
        print(
            "error: se requieren --name, --package y --destination",
            file=sys.stderr,
        )
        return 2

    return generate(args.name, args.package, Path(args.destination))


if __name__ == "__main__":
    sys.exit(main())
