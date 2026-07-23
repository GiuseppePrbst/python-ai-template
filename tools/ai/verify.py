"""Orquestador local de los quality gates de ``python-ai-template``.

Ejecuta, en este orden y deteniendose al primer fallo, los cuatro comandos
canonicos declarados en ``AGENTS.md`` y en ``docs/decisions.md`` (ADR-007):

    1. ``uv run ruff check .``
    2. ``uv run ruff format --check .``
    3. ``uv run pyright``
    4. ``uv run pytest``

Cada gate se invoca con ``subprocess.run`` recibiendo una lista de argumentos
(lista, sin ``shell=True`` y sin ``capture_output``), de forma que la salida
del subproceso se transmite en vivo a ``stdout`` y ``stderr`` exactamente
igual que si el usuario hubiera lanzado el comando directamente. Al fallar
un gate el script devuelve su ``exit code`` sin ejecutar los siguientes.

Uso canonico desde la raiz del repositorio::

    uv run python tools/ai/verify.py

Aunque ``verify.py`` se ejecute con ``uv run python ...``, invoca
explicitamente cada gate como ``uv run <herramienta>`` para que el contrato
sea identico en local y en CI.
"""

from __future__ import annotations

import subprocess
import sys

GATES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "ruff check",
        ("uv", "run", "ruff", "check", "."),
    ),
    (
        "ruff format --check",
        ("uv", "run", "ruff", "format", "--check", "."),
    ),
    (
        "pyright",
        ("uv", "run", "pyright"),
    ),
    (
        "pytest",
        ("uv", "run", "pytest"),
    ),
)


def _run_gate(label: str, argv: tuple[str, ...]) -> int:
    """Lanza un gate y devuelve su exit code.

    Imprime un encabezado visible con la etiqueta humana del gate y el comando
    exacto que se va a ejecutar, transmitiendo despues la salida del subproceso
    en vivo (no se captura ``stdout`` ni ``stderr``, no se usa ``shell=True``).
    """
    print(f">>> gate: {label}")
    print(f"    $ {' '.join(argv)}")
    print(f"    {'-' * 72}")
    sys.stdout.flush()
    completed = subprocess.run(argv)
    print(f"    {'-' * 72}")
    print(f"    exit code: {completed.returncode}")
    sys.stdout.flush()
    return completed.returncode


def main() -> int:
    """Ejecuta los gates en orden y devuelve el exit code del primer fallo."""
    print(f"Ejecutando {len(GATES)} quality gates desde {__file__}")
    print("=" * 72)
    for label, argv in GATES:
        rc = _run_gate(label, argv)
        if rc != 0:
            print("=" * 72, file=sys.stderr)
            print(
                f"FALLO: gate {label!r} salio con codigo {rc}; "
                "no se ejecutan los gates restantes.",
                file=sys.stderr,
            )
            return rc
    print("=" * 72)
    print(f"OK: los {len(GATES)} quality gates han pasado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
