"""Entry point para el console script ``python-ai-template``.

En esta primera unidad solo se implementa el subcomando ``audit``.
Cualquier otro argumento o subcomando devuelve exit code ``2``.

El subcomando ``audit`` se delega en
:mod:`python_ai_template.audit.cli`. Su contrato exacto se describe en
``docs/architecture.md`` y en el comando ``.opencode/commands/verify.md``.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = tuple(sys.argv[1:])
    if not argv:
        print(
            "uso: python-ai-template audit <repository> [--output <path>]",
            file=sys.stderr,
        )
        return 2
    subcommand = argv[0]
    if subcommand == "audit":
        from python_ai_template.audit.cli import main as audit_main

        return audit_main(list(argv[1:]))
    print(
        f"error: subcomando desconocido {subcommand!r}; "
        "solo se admite 'audit' en esta unidad",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
