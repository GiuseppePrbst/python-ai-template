# Arquitectura

Estado vigente de la arquitectura del repositorio generador y de sus límites.
Este documento se mantiene coherente con el código real y con
`docs/decisions.md`. Si hay divergencia, prevalece el código y se actualiza
este archivo.

## Resumen

`python-ai-template` es una **plantilla generadora** de proyectos Python
mínimos con layout `src/`. El repositorio no entrega un paquete instalable:
expone un generador (`tools/new_project.py`) que produce un proyecto
independiente a partir de los archivos parametrizados en `template/`.

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

- `tools/new_project.py`: generador ejecutable. Punto de entrada único para
  producir un proyecto nuevo. Solo usa `pathlib`, `argparse`, `tempfile`,
  `shutil` y `keyword` de la biblioteca estándar.
- `template/`: árbol de archivos que se copian al proyecto generado.
  - `pyproject.toml.tmpl`: configuración de `uv`, `ruff`, `pyright` y
    `pytest` del proyecto generado. Usa `{{DISTRIBUTION_NAME}}` para
    `[project].name` y `{{PACKAGE_NAME}}` para `[tool.hatch.build.targets.wheel]
    packages`.
  - `README.md.tmpl`: documentación visible del proyecto generado. Usa
    `{{PROJECT_NAME}}` y `{{PACKAGE_NAME}}`.
  - `.gitignore`: patrones de ignorado del proyecto generado.
  - `AGENTS.md`: reglas operativas para los agentes del proyecto generado.
  - `opencode.jsonc`: configuración de OpenCode del proyecto generado.
  - `.opencode/`: agentes, comandos y skills de OpenCode del proyecto
    generado. Incluye un `.opencode/.gitignore` que excluye artefactos de
    instalación local (`node_modules`, `package*.json`, `bun.lock*`).
  - `docs/`: documentación estructurada del proyecto generado
    (arquitectura, decisiones, errores, glosario, pendientes, estado,
    IA). En el proyecto generado los placeholders ya están sustituidos.
  - `src/__package_name__/`: código fuente del proyecto generado
    (`__init__.py.tmpl`).
  - `tests/test_smoke.py.tmpl`: smoke test del proyecto generado.
- `tests/test_new_project.py`: tests del generador.
- `pyproject.toml`: configuración del propio repositorio generador. Usa
  `[tool.uv] package = false` para que `uv sync` no intente construir un
  wheel del repositorio generador (que no es un paquete instalable). El
  build system sigue siendo hatchling por compatibilidad.
- `README.md`: descripción del repositorio generador y guía de uso.
- `AGENTS.md`: reglas operativas para cualquier agente que trabaje en este
  repositorio.
- `docs/`: documentación estructurada del repositorio generador.
- `opencode.jsonc`: configuración de OpenCode del repositorio generador.
- `.opencode/`: agentes, comandos y skills de OpenCode del repositorio
  generador.

## Límites vigentes

- El repositorio no entrega un paquete instalable. `uv sync` resuelve las
  dependencias de desarrollo (`ruff`, `pyright`, `pytest`) pero no intenta
  construir un wheel.
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

- **Runtime del generador**: ninguna. El generador usa solo la biblioteca
  estándar de Python.
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

1. Generación de un proyecto independiente.
2. Dentro del proyecto generado:
   - `uv sync`
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run pyright`
   - `uv run pytest`

Los tests unitarios del generador son necesarios pero no sustituyen este
E2E semántico. El defecto documentado en `docs/mistakes.md` ilustra por
qué: pasó los tests unitarios y solo se detectó al ejecutar `uv sync`
sobre el proyecto generado con un nombre visible con espacios.

## Cambios que requieren aprobación explícita

Cualquier cambio que:

- Añada una dependencia de runtime al generador.
- Modifique la API pública de `tools/new_project.py` (firma, argumentos,
  códigos de salida, comportamiento de staging).
- Introduzca un nuevo módulo en `tools/` o subdivida los existentes.
- Cambie la configuración de calidad del repositorio generador (`ruff`,
  `pyright`, `pytest`).
- Cambie la configuración de OpenCode del proyecto o del global.
- Modifique la estructura de `template/` o el conjunto de placeholders.
- Modifique los límites entre el generador, la plantilla y los proyectos
  generados.
