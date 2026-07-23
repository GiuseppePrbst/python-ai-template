# Arquitectura

Estado vigente de la arquitectura del repositorio generador y de sus límites.
Este documento se mantiene coherente con el código real y con
`docs/decisions.md`. Si hay divergencia, prevalece el código y se actualiza
este archivo.

## Resumen

`python-ai-template` es una **plantilla generadora** de proyectos Python
mínimos con layout `src/`. El repositorio es un **paquete instalable** que
produce proyectos independientes a partir de la plantilla empaquetada
como `package data` dentro del propio paquete.

Hay dos formas equivalentes de invocar el generador:

- **Console script instalado**: `uv tool install .` deja
  `new-python-project` disponible en `PATH` desde cualquier directorio.
  Representa la versión del paquete instalada en el toolchain.
- **Shim local** (`tools/new_project.py`): añade `<repo>/src` al
  `sys.path` y delega en `python_ai_template.cli.main`. Representa el
  checkout local y se usa durante el desarrollo sin instalar.

El generador usa solo la biblioteca estándar de Python, valida sus
argumentos, escribe archivos UTF-8 sin BOM con finales de línea LF, y mueve
el resultado desde un staging temporal al destino final solo tras pasar
todas las validaciones.

## Tres nombres

El generador distingue tres conceptos. Ver ADR-008 para el contexto y
ADR-008 para las alternativas consideradas.

- **`{{PROJECT_NAME}}`** — nombre visible entregado por `--name`. Puede
  contener espacios. Se usa en `README.md`, en los docstrings visibles y en
  los textos de la documentación del proyecto generado. No se normaliza: se
  conserva tal cual el usuario lo entrega.
- **`{{PACKAGE_NAME}}`** — nombre importable entregado por `--package`.
  Debe ser `str.isidentifier()`, no keyword de Python, solo ASCII, y no
  puede contener puntos, guiones, espacios ni separadores de ruta. Se usa
  en `src/<paquete>/`, en los imports, en `[tool.hatch.build.targets.wheel]
  packages` y en cualquier configuración de hatchling que apunte al paquete.
- **`{{DISTRIBUTION_NAME}}`** — nombre técnico derivado internamente de
  `{{PACKAGE_NAME}}` mediante `package_name.lower().replace("_", "-")`.
  El resultado se valida con la expresión regular
  `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Si no cumple el patrón, el generador
  falla antes de escribir. Se usa exclusivamente en `[project].name` de
  `pyproject.toml`. No es un argumento CLI.

## Componentes

- `src/python_ai_template/`: paquete instalable con la lógica del
  generador.
  - `__init__.py`: expone `__version__ = "0.1.0"`. Única fuente de verdad
    para `--version` y los metadatos del wheel.
  - `cli.py`: interfaz de línea de comandos. Construye el `ArgumentParser`
    con `--version` (vía `argparse`'s built-in `action="version"`),
    `--help`, `--name`, `--package` y `--destination`. Su `main(argv)`
    valida que los argumentos obligatorios estén presentes y delega en
    `generator.generate`.
  - `generator.py`: núcleo del generador. Define las validaciones
    (`_validate_name`, `_validate_package`, `_check_unresolved_placeholders`,
    `_check_forbidden_opencode_artifacts`, `_check_sensitive_files`,
    `_check_required_paths`), la sustitución de placeholders (`_render`),
    el cálculo de rutas de destino (`_compute_dest_path`) y la
    `generate()`. Localiza la plantilla con
    `_template_root()` que devuelve
    `importlib.resources.files("python_ai_template").joinpath("template")`.
    La función `_walk_template` recorre el `Traversable` recursivamente
    en orden determinista (orden lexicográfico por nombre en cada
    nivel) y emite tuplas `(Path relativo, Traversable)` para cada
    archivo, conservando literalmente nombres como `.gitignore`,
    `.opencode`, `__package_name__` y archivos `.tmpl`. No materializa
    la plantilla a un segundo directorio temporal: lee cada entrada
    directamente del `Traversable` y la escribe en el staging.
  - `template/`: árbol parametrizado que se copia a cada proyecto
    generado. Vive dentro del paquete para que el wheel la incluya y
    sea localizable con `importlib.resources`. Contiene los mismos
    archivos que en la fase 3 (`pyproject.toml.tmpl`, `README.md.tmpl`,
    `__init__.py.tmpl`, `test_smoke.py.tmpl`, `.gitignore`, `AGENTS.md`,
    `opencode.jsonc`, `.opencode/`, `docs/`), ahora bajo
    `src/python_ai_template/template/`.
- `tools/new_project.py`: shim de compatibilidad. Añade `<repo>/src` al
  principio de `sys.path`, importa `python_ai_template.cli.main` y termina
  con `raise SystemExit(main())`. Representa el checkout local; no intenta
  caer a una versión instalada del paquete.
- `tests/test_new_project.py`: tests del generador y de la CLI. Cubre
  tanto `python_ai_template.generator` como `python_ai_template.cli.main`
  (incluye `--version`, `--help`, argumentos de generación, argumentos
  faltantes y errores de validación).
- `pyproject.toml`: configuración del repositorio generador. Declara el
  paquete `python-ai-template` (versión `0.1.0`) con `requires-python =
  ">=3.12"`, registra el console script
  `new-python-project = "python_ai_template.cli:main"`, configura
  hatchling para construir un wheel desde
  `src/python_ai_template/`, y mantiene `ruff`, `pyright` y `pytest`
  como dev-deps.
- `README.md`: descripción del repositorio generador y guía de uso.
- `AGENTS.md`: reglas operativas para cualquier agente que trabaje en este
  repositorio.
- `docs/`: documentación estructurada del repositorio generador.
- `opencode.jsonc`: configuración de OpenCode del repositorio generador.
- `.opencode/`: agentes, comandos y skills de OpenCode del repositorio
  generador.

## Límites vigentes

- El repositorio entrega un paquete instalable. `uv tool install .` deja
  disponible el console script `new-python-project`. `uv sync` resuelve
  las dev-deps (`ruff`, `pyright`, `pytest`) y construye el paquete en
  modo editable.
- Hay dos puntos de entrada al generador: el console script
  `new-python-project` (versión instalada) y el shim
  `tools/new_project.py` (versión de desarrollo desde el checkout local).
  Ambos terminan en `python_ai_template.cli.main`.
- El paquete no tiene dependencias de runtime. Solo biblioteca estándar
  (`argparse`, `keyword`, `re`, `shutil`, `sys`, `tempfile`,
  `importlib.resources`, `pathlib`).
- La plantilla viaja dentro del paquete como `package data` y se accede
  con `importlib.resources.files("python_ai_template").joinpath("template")`.
  No depende del directorio de trabajo ni de la ruta del repositorio.
- El generador no ejecuta `uv`, `git` ni ningún otro comando externo.
- El generador no modifica archivos fuera del directorio destino. No toca
  el repositorio actual ni repositorios git existentes.
- El generador rechaza destinos existentes. No sobrescribe ni mezcla
  contenido.
- La configuración de IA vive en `opencode.jsonc` (proyecto) y en
  `~/.config/opencode/opencode.json` (global). El modelo, provider y API
  key se definen en el global; el proyecto nunca debe duplicar secretos.
- Los archivos `AGENTS.md`, `docs/` y `.opencode/` definen la operativa de
  los agentes. Cualquier cambio en esos archivos se trata como cambio de
  arquitectura.
- La plantilla parametrizada contiene los placeholders `{{PROJECT_NAME}}`,
  `{{PACKAGE_NAME}}` y `{{DISTRIBUTION_NAME}}`. Si tras la generación
  queda cualquier patrón `{{...}}` sin sustituir, el generador falla sin
  crear el destino final.

## Dependencias

- **Runtime del paquete `python-ai-template`**: ninguna. El paquete y el
  console script usan solo la biblioteca estándar de Python.
- **Desarrollo del repositorio generador**: `pyright`, `pytest`, `ruff`,
  gestionadas con `uv` como dev-dependencies.
- **Runtime de los proyectos generados**: ninguna declarada por defecto.
  Cada proyecto generado puede añadir las suyas siguiendo las prácticas de
  `AGENTS.md` y `docs/decisions.md`.

## Fuera de alcance

- Copier, Cookiecutter u otros motores de plantillas externos. El
  generador se implementa desde cero con la biblioteca estándar.
- Integraciones con proveedores de IA más allá de los definidos por la
  configuración global de OpenCode.
- Publicación de paquetes. Ni el repositorio generador ni los proyectos
  generados están pensados para publicarse en PyPI.
- Múltiples paquetes Python dentro del mismo repositorio generado.
- Infraestructura remota (servicios web, bases de datos, colas, etc.) en
  los proyectos generados.

## Criterio de aceptación: E2E obligatorio

Un cambio en el generador o en la plantilla **no se considera terminado**
hasta ejecutar, con datos representativos (incluido un nombre visible con
espacios):

1. Validacion del repositorio generador con sus cuatro quality gates.
2. Construccion del wheel y verificacion de que el archivo
   `python_ai_template/template/` y sus archivos ocultos (`.gitignore`,
   `.opencode/.gitignore`, `__package_name__`, `.tmpl`) estan dentro.
3. Instalacion con `uv tool install .` y validacion de
   `new-python-project --version` y `new-python-project --help`.
4. Generacion de un proyecto independiente desde un directorio que **no
   pertenezca al repositorio** (p. ej. `/tmp`).
5. Dentro del proyecto generado:
   - `uv sync`
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run pyright`
   - `uv run pytest`
6. Validacion manual del shim local con
   `python3 tools/new_project.py --version` y `--help` desde la raiz
   del repositorio.
7. Desinstalacion limpia con `uv tool uninstall python-ai-template`.

Los tests unitarios del generador son necesarios pero no sustituyen este
E2E semántico. El defecto documentado en `docs/mistakes.md` ilustra por
qué: pasó los tests unitarios y solo se detectó al ejecutar `uv sync`
sobre el proyecto generado con un nombre visible con espacios.

## Cambios que requieren aprobación explícita

Cualquier cambio que:

- Añada una dependencia de runtime al paquete.
- Modifique la API pública de `python_ai_template.cli.main` (firma,
  argumentos, códigos de salida) o de `python_ai_template.generator.generate`.
- Introduzca un nuevo módulo en `src/python_ai_template/` o subdivida los
  existentes.
- Modifique el comportamiento del shim `tools/new_project.py` (sys.path,
  import target, terminación).
- Cambie la configuración de calidad del repositorio generador (`ruff`,
  `pyright`, `pytest`).
- Cambie la configuración de OpenCode del proyecto o del global.
- Modifique la estructura de la plantilla (`src/python_ai_template/template/`)
  o el conjunto de placeholders.
- Modifique los límites entre el paquete, la plantilla, los proyectos
  generados y el shim.
