#!/usr/bin/env python3
"""Shim de compatibilidad para el generador.

La implementacion vive en ``python_ai_template.cli`` y la plantilla
viaja como ``package data`` dentro de ``python_ai_template``. Este
shim existe para que ``python3 tools/new_project.py`` siga
funcionando desde dentro del repositorio, representando el checkout
local. El console script ``new-python-project`` representa la version
instalada mediante ``uv tool install`` y no se ve afectado por este
archivo.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"

if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from python_ai_template.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
