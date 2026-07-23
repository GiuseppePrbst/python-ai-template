# Pendientes

Lista priorizada de tareas pendientes. Se actualiza con `/handoff` y se revisa al inicio de cada sesion junto con `docs/current-state.md`.

## Alta prioridad

- (vacio)

## Prioridad media

- (vacio)

## Prioridad baja

- Decidir si se quiere un test E2E que invoque
  `python_ai_template.cli.main` como subproceso desde `tests/`, ademas de
  los tests que importan el modulo directamente.

## Backlog

- Evaluar, tras suficientes ciclos de uso, si conviene introducir un segundo modelo de escalamiento mas alla del premium actual.
- Definir metricas concretas y umbrales para `docs/ai/evaluations.md` cuando haya datos suficientes.
- Revisar periodicamente si la configuracion global de OpenCode (`~/.config/opencode/opencode.json`) sigue alineada con `docs/decisions.md` (ADR-002, ADR-003, ADR-006).
- Si en el futuro el paquete expone una API programatica estable para consumidores externos, evaluar la inclusion del marcador `py.typed` (PEP 561) y documentarlo en una nueva ADR. No se anadio en la fase 4 por decision explicita.
