# python-ai-template

Plantilla generadora de proyectos Python compatibles con el stack de desarrollo
asistido por IA. A partir de este repositorio se generan proyectos nuevos
ejecutando `tools/new_project.py`.

## Requisitos

- Python 3.12 o superior.
- `uv` para ejecutar las validaciones (opcional; se usa si está instalado).

## Estructura

- `template/`: archivos parametrizados que se copian al proyecto generado.
  Contiene los placeholders `{{PROJECT_NAME}}`, `{{PACKAGE_NAME}}` y
  `{{DISTRIBUTION_NAME}}`. El directorio `__package_name__` se renombra al
  nombre del paquete.
- `tools/new_project.py`: generador ejecutable, solo biblioteca estándar.
- `tests/test_new_project.py`: tests del generador.
- `docs/`: documentación del propio repositorio generador.
- `pyproject.toml`: configuración de `uv`, `ruff`, `pyright` y `pytest` para
  el repositorio generador (no entrega un paquete instalable).

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

Ejemplo:

```bash
python3 tools/new_project.py \
  --name "E2E Smoke" \
  --package e2e_smoke \
  --destination /ruta/e2e-smoke
```

Tras la generación, el generador imprime los próximos pasos:

```bash
cd /ruta/e2e-smoke
uv sync
```

El generador **no** ejecuta `uv sync` ni ningún otro comando externo. Tampoco
realiza commits ni modifica repositorios git existentes.

## Validación del repositorio generador

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

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
