# Estado actual

Estado del repositorio al cierre de esta sesion. Este archivo se reescribe
con `/handoff` al final de cada bloque de trabajo. Debe permitir retomar
el trabajo sin la conversacion previa.

## Objetivo

Incorporar CI reproducible y herramientas locales de verificacion al
repositorio sin modificar el comportamiento del generador (hardening
operativo v0.3.0).

## Estado

- Repositorio en src layout, paquete `python-ai-template` version `0.2.2`.
- `template/` vive dentro del paquete y se accede via `importlib.resources`.
- Console script `new-python-project` registrado.
- Tests: 33 casos aprobados.
- Scripts locales nuevos (contrato comun local/CI):
  - `tools/ai/verify.py` orquesta los cuatro quality gates y se detiene al
    primer fallo propagando su `exit code`.
  - `tools/ai/verify_wheel.py` verifica la consistencia de las cuatro fuentes
    de la version y la presencia de los cinco recursos obligatorios de la
    plantilla en el wheel, usando solo biblioteca estandar.
- Pipeline de CI remoto:
  - Workflow `.github/workflows/ci.yml` con triggers `push` y
    `pull_request`, `permissions: contents: read`, `strategy.fail-fast:
    false`, matriz `quality` en Python 3.12 y 3.14, y job `package`
    dependiente que construye wheel + sdist, ejecuta `verify_wheel.py` y
    sube exactamente un artifact `dist` (con `if-no-files-found: error`,
    `retention-days: 14`).
  - Actions ancladas a SHA completo con tag como comentario:
    `actions/checkout@v7.0.1`, `astral-sh/setup-uv@v8.1.0`,
    `actions/upload-artifact@v7.0.1`.
- CI remoto aprobado en run `30041232754` con los tres jobs en verde:
  - `quality` Python 3.12: pass.
  - `quality` Python 3.14: pass.
  - `package`: pass (wheel + sdist + artifact `dist`, tamano 91715 bytes,
    no expirado).
- Validacion local reproduce el contrato remoto:
  - `uv run python tools/ai/verify.py`: pass (los cuatro gates en verde).
  - `uv build` + `uv run python tools/ai/verify_wheel.py`: pass
    (cuatro fuentes de version coinciden; cinco recursos obligatorios
    presentes).
- Decisiones: ADR-011 anadida (`docs/decisions.md`) sobre el hardening
  operativo, los scripts locales, la matriz quality, el job package
  unico, el artifact unico y las Actions fijadas por SHA.
- Documentacion actualizada: `README.md` (badge CI + atajo canonico),
  `AGENTS.md` (orquestador canonico), `.opencode/commands/verify.md`
  (orquestador + validacion de empaquetado), `docs/architecture.md`
  (seccion "Pipeline de validacion reproducible (CI/local)"),
  `docs/todos.md` (CI hardening completado, tareas menores registradas),
  `docs/ai/evaluations.md` (primera entrada del registro).

## Archivos creados o modificados en este bloque

- `tools/ai/verify.py` (nuevo): orquestador local de los cuatro gates.
- `tools/ai/verify_wheel.py` (nuevo): verificador del wheel.
- `.github/workflows/ci.yml` (nuevo): pipeline de CI reproducible.
- `README.md` (modificado): anadido badge CI y seccion de validacion
  con el atajo canonico; conservados los cuatro gates visibles.
- `AGENTS.md` (modificado): el atajo `uv run python tools/ai/verify.py`
  queda documentado junto a los cuatro gates; `/verify` apunta al
  orquestador.
- `.opencode/commands/verify.md` (modificado): paso 1 pasa a ser el
  orquestador; paso 2 anade la validacion del empaquetado.
- `docs/architecture.md` (modificado): nueva seccion "Pipeline de
  validacion reproducible (CI/local)" tras los limites vigentes.
- `docs/decisions.md` (modificado): anadida ADR-011 sin reescribir las
  anteriores.
- `docs/current-state.md` (reescrito): este archivo.
- `docs/todos.md` (modificado): CI hardening marcado como completado;
  nuevas tareas de prioridad baja registradas.
- `docs/ai/evaluations.md` (modificado): primera entrada concreta del
  registro.

No se modificaron: `pyproject.toml`, `uv.lock`, `src/python_ai_template/`,
`tools/new_project.py`, `tests/`, `.gitignore`, `.opencode/agents/`,
`.opencode/skills/`, `opencode.jsonc`, `docs/ai/model-policy.md`,
`docs/ai/context-policy.md`, `docs/glossary.md`, `docs/mistakes.md`.

## Validaciones

Repositorio generador:

- `ruff check`: pass.
- `ruff format --check`: pass.
- `pyright`: pass.
- `pytest`: 33 passed.

Orquestador local:

- `uv run python tools/ai/verify.py`: pass (los cuatro gates en verde,
  exit code 0).

Wheel:

- `uv build`: produce `dist/python_ai_template-0.2.2-py3-none-any.whl` y
  `dist/python_ai_template-0.2.2.tar.gz`.
- `uv run python tools/ai/verify_wheel.py`: pass (cuatro fuentes de la
  version coinciden; cinco recursos obligatorios presentes).

CI remoto (run `30041232754`):

- `quality` (Python 3.12): pass.
- `quality` (Python 3.14): pass.
- `package`: pass.
- Artifact `dist` subido, 91715 bytes, no expirado.

## Decisiones

- ADR-011 anadida: hardening operativo v0.3.0. Scripts locales como
  contrato comun local/CI, matriz `quality` en Python 3.12 y 3.14, job
  `package` unico dependiente, artifact unico y Actions fijadas por SHA.

## Problemas pendientes

- Ninguno relativo al hardening operativo v0.3.0. Pendiente el commit
  del conjunto (documentacion + scripts + workflow) una vez que el
  usuario lo autorice.

## Proxima accion

El paquete sigue en `0.2.2`. Queda pendiente, en orden, cuando el usuario
lo autorice:

1. Bump de version: `project.version` en `pyproject.toml` y `__version__`
   en `src/python_ai_template/__init__.py` pasan a `0.3.0`, alineados con
   el tag.
2. Commit del conjunto (CI + scripts + documentacion) si se hace en bloque,
   o commits separados segun preferencia.
3. Creacion del tag `v0.3.0`.
4. Instalacion local del paquete desde la nueva version con
   `uv tool install .` y validacion de `new-python-project --version`.

Sin acciones adicionales del implementer hasta autorizacion.
