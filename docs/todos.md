# Pendientes

Lista priorizada de tareas pendientes. Se actualiza con `/handoff` y se
revisa al inicio de cada sesion junto con `docs/current-state.md`.

## Completadas recientemente

- **v0.3.2 — hardening de agentes y línea base de evaluación**
  (ADR-013). CI remota aprobada (run `30058735050`, jobs quality 3.12,
  quality 3.14 y package). Tag `v0.3.2` publicado (apunta a
  `f063fe2`). Instalación desde tag validada:
  `new-python-project --version` devuelve `0.3.2`, proyecto generado
  con 7 artefactos OpenCode distribuidos. Herramienta desinstalada
  correctamente. Working tree limpio al cierre. Cerrada.
- Capa de exploracion y compactacion v0.3.1 (ADR-012): agente `scout`,
  comando `/review` manual, skill `context-handoff`, plugin
  `structured-compaction`, version bump `0.3.0` -> `0.3.1`. CI remota
  aprobada. Tag `v0.3.1` publicado. Instalacion desde tag validada.
  Working tree limpio al cierre. Cerrada.
- CI hardening operativo v0.3.0 (ADR-011, scripts `tools/ai/verify.py`
  y `tools/ai/verify_wheel.py`, workflow `.github/workflows/ci.yml`,
  documentacion asociada). CI remoto aprobado (run `30041232754`).
  Tag `v0.3.0` creado, instalacion local desde tag validada,
  `new-python-project --version` devuelve `0.3.0`. Cerrada.

## Prioridad media

- Tras la primera sesion interactiva real con OpenCode 1.18.4 y el
  plugin `structured-compaction`, registrar en `docs/mistakes.md`
  cualquier desviacion observada entre el contrato del plugin (solo
  anexa a `output.context`, no escribe, no usa shell, no genera logs)
  y la realidad, incluyendo el caso "hook no disponible", que
  requeriria una nueva ADR.
- Ejecutar `/compact-test` sobre el plugin vigente y registrar el
  resultado con `record_evaluation.py`. Si la compactacion no se
  dispara por umbral ni por comando soportado, registrar
  `inconclusive`. Repetir tras cualquier cambio al plugin o al
  formato canonico de `current-state.md`.

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
- Si en el futuro el plugin `structured-compaction` necesita anexar
  varias entradas a `output.context` o aparecer mas de una vez por
  compactacion, evaluar si conviene un wrapper que centralice las
  inyecciones en lugar de multiplicar `output.context.push(...)` desde
  el plugin.

## Trabajo posterior (no incluido en v0.3.2)

- Telemetria externa y routing adaptativo siguen fuera de alcance.
  Cualquier integracion futura con proveedores o almacenes de
  memoria requiere una ADR propia y actualizacion de
  `docs/ai/model-policy.md`.
- Si en el futuro el plugin `structured-compaction` crece mas alla
  de la forma estructural protegida por `verify_opencode.py` (mas
  hooks, mas imports, logica dinamica), evaluar si conviene
  actualizar el validador o dividirlo en modulos por hook.
- Si OpenCode 1.18.4 expone un mecanismo soportado y verificable
  para forzar compactacion, evaluar la automatizacion parcial de
  `/compact-test` y documentarlo en una nueva ADR sin reintroducir
  dependencias externas.

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
- Si en el futuro OpenCode 1.18.4 expone un hook estable para
  compactacion (o se desactiva `experimental.session.compacting`),
  reevaluar ADR-012 y decidir si el plugin queda obsoleto o se
  renueva sobre la nueva API.
