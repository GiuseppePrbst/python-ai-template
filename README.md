# python-ai-template

[![CI](https://github.com/GiuseppePrbst/python-ai-template/actions/workflows/ci.yml/badge.svg)](https://github.com/GiuseppePrbst/python-ai-template/actions/workflows/ci.yml)

Plantilla generadora de proyectos Python compatibles con el stack de desarrollo
asistido por IA. A partir de este repositorio se generan proyectos nuevos
ejecutando el console script `new-python-project` (tras `uv tool install .`)
o el shim local `tools/new_project.py` (desde el checkout).

## Requisitos

- Python 3.12 o superior.
- `uv` para ejecutar las validaciones y para `uv tool install`.

## Estructura

- `src/python_ai_template/`: paquete instalable.
  - `__init__.py`: expone `__version__ = "0.1.0"`.
  - `cli.py`: define el console script `new-python-project` con `--name`,
    `--package`, `--destination`, `--version` y `--help`.
  - `generator.py`: nucleo del generador. Accede a la plantilla con
    `importlib.resources.files("python_ai_template").joinpath("template")`
    y la recorre con un walker determinista que conserva nombres como
    `.gitignore`, `.opencode`, `__package_name__` y archivos `.tmpl`.
  - `template/`: archivos parametrizados que se copian al proyecto
    generado. Contiene los placeholders `{{PROJECT_NAME}}`,
    `{{PACKAGE_NAME}}` y `{{DISTRIBUTION_NAME}}`. El directorio
    `__package_name__` se renombra al nombre del paquete.
- `tools/new_project.py`: shim determinista. Anade `<repo>/src` al
  `sys.path`, importa `python_ai_template.cli.main` y termina con
  `raise SystemExit(main())`. Representa el checkout local.
- `tests/test_new_project.py`: tests del generador y de la CLI.
- `docs/`: documentacion del propio repositorio generador.
- `pyproject.toml`: configuracion de `uv`, `ruff`, `pyright` y `pytest`,
  registro del console script y `[tool.hatch.build.targets.wheel]
  packages = ["src/python_ai_template"]`.

## Uso del generador

El generador distingue **tres nombres** (ver ADR-008):

- `--name` es el **nombre visible** (`{{PROJECT_NAME}}`). Puede contener
  espacios y se usa en `README.md`, docstrings y textos visibles.
- `--package` es el **paquete Python** (`{{PACKAGE_NAME}}`). Debe ser un
  identificador Python válido, no keyword, solo ASCII, y se usa en `src/`,
  imports y configuración de paquetes.
- El **nombre de distribución** (`{{DISTRIBUTION_NAME}}`) se deriva
  automáticamente del paquete: se pone en minúsculas y se reemplaza `_` por
  `-`. Por ejemplo, `e2e_smoke` produce `e2e-smoke`. Se usa exclusivamente
  en `[project].name` de `pyproject.toml`. **No existe un argumento
  separado** para el nombre de distribución: se deriva siempre del
  paquete y se valida con la expresión regular
  `^[a-z0-9]+(?:-[a-z0-9]+)*$`.

### Forma recomendada: console script

Tras `uv tool install .`, el comando `new-python-project` queda disponible
en `PATH` desde cualquier directorio:

```bash
new-python-project \
  --name "Mi Proyecto" \
  --package mi_proyecto \
  --destination ~/projects/mi-proyecto
```

### Forma local: shim de desarrollo

Desde la raiz del repositorio, sin instalar el paquete, se puede invocar
el shim:

```bash
python3 tools/new_project.py \
  --name "E2E Smoke" \
  --package e2e_smoke \
  --destination /ruta/e2e-smoke
```

El shim siempre representa el checkout local, no una version instalada.

### Opciones comunes

- `--version` imprime `0.1.0` y termina con codigo 0.
- `--help` imprime la ayuda y termina con codigo 0.

### Tras la generacion

El generador imprime los proximos pasos:

```bash
cd /ruta/e2e-smoke
uv sync
```

El generador **no** ejecuta `uv sync` ni ningun otro comando externo.
Tampoco realiza commits ni modifica repositorios git existentes.

## Validación del repositorio generador

Atajo canónico (orquesta los cuatro gates y se detiene en el primer fallo
propagando su `exit code`):

```bash
uv sync
uv run python tools/ai/verify.py
```

Detrás de este comando se ejecutan, en este orden, los cuatro gates
obligatorios:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

El script `tools/ai/verify.py` usa solo biblioteca estándar, invoca cada gate
con `subprocess.run` (lista, sin `shell=True`, sin `capture_output`) y
transmite la salida en vivo. Su contrato es idéntico en local y en CI.

Validación adicional del empaquetado (wheel + recursos):

```bash
rm -rf dist
uv build
uv run python tools/ai/verify_wheel.py
```

`verify_wheel.py` confirma que `pyproject.toml`, `__version__`, el nombre
del wheel y `METADATA Version` coinciden, y que el wheel contiene los
cinco recursos obligatorios de la plantilla.

## Validación E2E del generador

Un cambio en el generador o en la plantilla no se considera terminado hasta
ejecutar, con un nombre visible con espacios, dentro del proyecto generado:

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

Los tests unitarios del generador son necesarios pero no sustituyen este
E2E semántico. Ver `docs/mistakes.md` para el defecto que motivó esta
regla.

## Política de sustitución

- `{{PROJECT_NAME}}`: nombre visible del proyecto. Se conserva tal cual el
  usuario lo entrega, sin normalización.
- `{{PACKAGE_NAME}}`: nombre del paquete Python. Debe ser un identificador
  Python válido, no keyword, solo ASCII.
- `{{DISTRIBUTION_NAME}}`: nombre de distribución derivado de
  `{{PACKAGE_NAME}}`. Se valida con la expresión regular
  `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Si la derivación no cumple el patrón, el
  generador falla antes de escribir.
- `__package_name__` (en nombres de directorio y archivo): se sustituye por
  el valor de `--package`.

## Política de destino

- El destino final no debe existir. Si existe, aunque esté vacío, el
  generador lo rechaza.
- Si la ruta padre no existe, se crea.
- La generación se realiza primero en un staging temporal dentro del mismo
  directorio padre del destino y solo se mueve al destino final tras pasar
  las validaciones.
- Si ocurre un error, el staging se elimina y el destino final no se crea.

## Privacidad y secretos

El generador no introduce secretos, claves, tokens ni configuración global
de OpenCode en los proyectos generados. Ver `AGENTS.md` y `docs/decisions.md`
para más detalles.
