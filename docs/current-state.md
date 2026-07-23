# Estado actual

Estado del repositorio al cierre de esta sesion. Este archivo se reescribe
con `/handoff` al final de cada bloque de trabajo. Debe permitir retomar
el trabajo sin la conversacion previa.

## Objetivo

Convertir `python-ai-template` en un paquete instalable con src layout,
distribuible via `uv tool install` y con un console script
`new-python-project` ejecutable desde cualquier directorio.

## Estado

- Repositorio migrado a src layout: `src/python_ai_template/`.
- `template/` movido a `src/python_ai_template/template/` y accesible con
  `importlib.resources.files("python_ai_template").joinpath("template")`.
- Generador reorganizado en `python_ai_template.generator` y
  `python_ai_template.cli`.
- Console script `new-python-project = "python_ai_template.cli:main"`
  registrado en `pyproject.toml`.
- Shim local `tools/new_project.py` conserva `python3 tools/new_project.py
  ...` para uso desde el checkout.
- Tests: 33 casos aprobados (28 de regresion + 5 de `cli.main`:
  `--version`, `--help`, generacion, argumentos faltantes, error de
  validacion).
- Wheel construido y verificado: contiene todos los archivos obligatorios
  de la plantilla, incluidos `.gitignore` y `.opencode/.gitignore`.
- `uv tool install .` deja `new-python-project` disponible en `PATH`.
- E2E desde `/tmp` con un proyecto generado completo: pasa `uv sync`,
  `ruff check`, `ruff format --check`, `pyright` y `pytest`.
- Shim local validado manualmente con `--version` y `--help`.
- `uv tool uninstall python-ai-template` deja el sistema limpio.

## Archivos modificados o creados

- `src/python_ai_template/__init__.py` (nuevo): expone `__version__ =
  "0.1.0"`.
- `src/python_ai_template/cli.py` (nuevo): argparse con `--version`,
  `--help`, `--name`, `--package` y `--destination`; delega en
  `generator.generate`.
- `src/python_ai_template/generator.py` (nuevo): nucleo del generador con
  acceso a la plantilla via `importlib.resources` y recorrido determinista
  via `_walk_template(Traversable)`.
- `src/python_ai_template/template/...` (movido completo desde `template/`):
  todos los archivos del directorio `template/` original, ahora dentro
  del paquete.
- `tools/new_project.py` (reescrito como shim determinista): anade
  `<repo>/src` a `sys.path`, importa `python_ai_template.cli.main`,
  termina con `raise SystemExit(main())`.
- `pyproject.toml` (modificado): anadido `[project.scripts]`,
  `[tool.hatch.build.targets.wheel] packages`; eliminado
  `[tool.uv] package = false`; ajustados `[tool.pyright]` y
  `[tool.pytest.ini_options]` para apuntar a `src/`.
- `tests/test_new_project.py` (modificado): importa
  `from python_ai_template import generator as new_project`; anadidos 5
  tests de `cli.main`.
- `README.md` (modificado): documenta `uv tool install .` y el console
  script; conserva la seccion legacy de `tools/new_project.py`.
- `docs/architecture.md` (modificado): refleja el src layout, los dos
  puntos de entrada, el wheel instalable y `importlib.resources`.
- `docs/decisions.md` (modificado): anadido ADR-010 sobre la migracion a
  paquete instalable.
- `docs/glossary.md` (modificado): anadidas entradas `python_ai_template`,
  `Console script`, `CLI`, `Shim local`, `src layout`, `package data`,
  `importlib.resources`, `Traversable`.

## Validaciones

Repositorio generador:

- `ruff check`: pass.
- `ruff format --check`: pass.
- `pyright`: pass.
- `pytest`: 33 passed.

Wheel:

- `uv build`: produce `dist/python_ai_template-0.1.0-py3-none-any.whl` con
  todos los archivos obligatorios de la plantilla, incluyendo `.gitignore`
  y `.opencode/.gitignore`.

Tool install:

- `uv tool install .`: instala el console script `new-python-project`.
- `new-python-project --version`: imprime `0.1.0`.
- `new-python-project --help`: imprime la ayuda con `--name`, `--package`,
  `--destination`, `--version` y `--help`.

E2E desde `/tmp`:

- `new-python-project --name "Installed Tool Smoke" --package
  installed_tool_smoke --destination /tmp/installed-tool-smoke`: genera
  el proyecto completo.
- Dentro de `/tmp/installed-tool-smoke`:
  - `uv sync`: pass.
  - `uv run ruff check .`: pass.
  - `uv run ruff format --check .`: pass.
  - `uv run pyright`: pass.
  - `uv run pytest`: 1 passed.

Shim local:

- `python3 tools/new_project.py --version`: imprime `0.1.0`.
- `python3 tools/new_project.py --help`: imprime la ayuda.

Limpieza:

- `uv tool uninstall python-ai-template`: deja el sistema limpio.

## Decisiones

- ADR-010 anadida: el repositorio pasa de plantilla generadora plana a
  paquete instalable con src layout, console script y shim local.

## Problemas pendientes

- Ninguno relativo a la fase 4. Pendiente el commit del conjunto una vez
  que el usuario lo autorice.

## Proxima accion

Esperar autorizacion del usuario para commit. Sin acciones adicionales
del implementer.
