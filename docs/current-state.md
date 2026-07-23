# Estado actual

Estado del repositorio al cierre de esta sesión. Este archivo se reescribe
con `/handoff` al final de cada bloque de trabajo. Debe permitir retomar el
trabajo sin la conversación previa.

## Objetivo

Corregir el defecto semántico detectado por el E2E y validar la plantilla
reusable.

## Estado

- Generador corregido.
- 28 tests aprobados.
- Quality gates del repositorio generador aprobados.
- Proyecto generado con `E2E Smoke` validado completamente.
- Reviewer detectó únicamente deuda documental, ahora en corrección.

## Archivos modificados o creados

- `tools/new_project.py`: introducido `{{DISTRIBUTION_NAME}}`, validación
  endurecida de `--package` (ASCII, regex de distribución) y try/except
  sobre la derivación.
- `tests/test_new_project.py`: añadidos los ocho casos del E2E.
- `template/pyproject.toml.tmpl`: `[project].name` usa
  `{{DISTRIBUTION_NAME}}`.
- `docs/mistakes.md`: entrada del defecto E2E fechada 2026-07-23.
- `docs/decisions.md`: ADR-008 ampliada con la distinción de los tres
  nombres, las alternativas consideradas y la referencia cruzada a
  `docs/mistakes.md`.
- `docs/architecture.md`: sección "Tres nombres", corrección de la
  afirmación obsoleta sobre `packages = []` por `[tool.uv] package = false`,
  documentación de los tres placeholders y sección "Criterio de
  aceptación: E2E obligatorio".
- `docs/current-state.md`: reescrito (este archivo).
- `README.md`: sección sobre los tres nombres y ejemplo de uso.
- `template/docs/glossary.md`: tres entradas separadas
  (`{{PROJECT_NAME}}`, `{{PACKAGE_NAME}}`, `{{DISTRIBUTION_NAME}}`).
- `template/docs/architecture.md`: sección "Tres nombres".
- `template/docs/decisions.md`: nota inicial indicando que las decisiones
  del repositorio generador se mantienen en el repositorio de la
  plantilla.

## Validaciones

Repositorio generador:

- `ruff check`: pass.
- `ruff format --check`: pass.
- `pyright`: pass.
- `pytest`: 28 passed.

Proyecto generado (con `--name "E2E Smoke" --package e2e_smoke`):

- `uv sync`: pass.
- `ruff check`: pass.
- `ruff format --check`: pass.
- `pyright`: pass.
- `pytest`: 1 passed.

## Decisiones

- ADR-008 ampliada con la distinción de los tres nombres
  (`{{PROJECT_NAME}}`, `{{PACKAGE_NAME}}`, `{{DISTRIBUTION_NAME}}`) y las
  alternativas descartadas.

## Problemas pendientes

- Revisión final del reviewer tras cerrar la documentación.
- Commit inicial de la plantilla.

## Próxima acción

Reejecutar reviewer, aprobar y crear el commit inicial.
