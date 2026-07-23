# Pendientes

Lista priorizada de tareas pendientes. Se actualiza con `/handoff` y se revisa al inicio de cada sesion junto con `docs/current-state.md`.

## Completadas recientemente

- CI hardening operativo v0.3.0 (ADR-011, scripts `tools/ai/verify.py` y
  `tools/ai/verify_wheel.py`, workflow `.github/workflows/ci.yml`,
  documentacion asociada). CI remoto aprobado en run `30041232754`.
  Pendiente solo: bump a `0.3.0`, commit, tag e instalacion local.

## Alta prioridad

- (vacio)

## Prioridad media

- (vacio)

## Prioridad baja

- Evitar la duplicacion del mensaje en algunas rutas de
  `tools/ai/verify_wheel.py` (en `_verify` se imprime `error: ...` en
  stderr y `main` vuelve a imprimir `verificacion del wheel FALLIDA:
  ...` para la misma excepcion). Considerar mover la impresion del
  prefijo a `main` y dejar que `_verify` solo lance.
- Considerar admitir `ast.AnnAssign` en `_read_package_version` de
  `tools/ai/verify_wheel.py` por si en el futuro `__version__` se
  declara con anotacion de tipo (`__version__: str = "0.3.0"`). El
  `__init__.py` actual usa asignacion simple, por lo que no afecta al
  estado vigente.
- Evaluar la inclusion de `concurrency:` en `.github/workflows/ci.yml`
  para cancelar runs anteriores cuando llegue un push mas reciente a la
  misma rama o al mismo PR, si el volumen de ejecuciones lo justifica.
- Evaluar filtros de `branches:` y `types:` en los triggers
  `push` y `pull_request` del workflow cuando aumente el volumen de
  pushes o de PRs automatizados.

## Trabajo posterior (no incluido en v0.3.0)

- Pre-commit: queda fuera de alcance del hardening operativo v0.3.0. Si
  en el futuro se justifica, abordarlo en una ADR propia, evaluando
  secret scanning, formato automatico y ganchos sobre `tools/ai/`,
  `pyproject.toml` y `.github/workflows/`.

## Backlog

- Decidir si se quiere un test E2E que invoque
  `python_ai_template.cli.main` como subproceso desde `tests/`, ademas de
  los tests que importan el modulo directamente.
- Evaluar, tras suficientes ciclos de uso, si conviene introducir un segundo modelo de escalamiento mas alla del premium actual.
- Definir metricas concretas y umbrales para `docs/ai/evaluations.md` cuando haya datos suficientes.
- Revisar periodicamente si la configuracion global de OpenCode (`~/.config/opencode/opencode.json`) sigue alineada con `docs/decisions.md` (ADR-002, ADR-003, ADR-006).
- Si en el futuro el paquete expone una API programatica estable para consumidores externos, evaluar la inclusion del marcador `py.typed` (PEP 561) y documentarlo en una nueva ADR. No se anadio en la fase 4 por decision explicita.
- Si en el futuro el wheel lleva build tag explicito (PEP 427), revisar el
  parser `parts[1:-3]` de `tools/ai/verify_wheel.py` para distinguir
  build tag de version. Hoy basta porque no se usan build tags.
