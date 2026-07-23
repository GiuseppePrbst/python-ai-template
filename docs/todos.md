# Pendientes

Lista priorizada de tareas pendientes. Se actualiza con `/handoff` y se revisa al inicio de cada sesión junto con `docs/current-state.md`.

## Alta prioridad

- (vacío)

## Prioridad media

- Validar el generador con un proyecto generado en una ruta fuera de este repositorio y ejecutar allí los cuatro quality gates.

## Prioridad baja

- Decidir si se quiere un test E2E que invoque
  `tools/new_project.py` como subproceso desde `tests/`, además de los
  tests que importan el módulo directamente.

## Backlog

- Evaluar, tras suficientes ciclos de uso, si conviene introducir un segundo modelo de escalamiento más allá del premium actual.
- Definir métricas concretas y umbrales para `docs/ai/evaluations.md` cuando haya datos suficientes.
- Revisar periódicamente si la configuración global de OpenCode (`~/.config/opencode/opencode.json`) sigue alineada con `docs/decisions.md` (ADR-002, ADR-003, ADR-006).
