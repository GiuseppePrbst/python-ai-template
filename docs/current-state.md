# Estado actual

Estado del repositorio al cierre de la sesión v0.3.2. Este archivo se reescribe con `/handoff` al final de cada bloque de trabajo siguiendo el formato canónico definido en la skill `context-handoff`. Permite retomar el trabajo sin la conversación previa.

## Objetivo actual

Cerrar v0.3.2 (ADR-013): hardening de agentes y línea base de evaluación. El código está commitado en `aea6630` con versión `0.3.2`, los cinco quality gates pasan localmente (121 tests, 8/8 invariantes), el wheel se verifica con 12 recursos. Pendiente: CI remota, tag e instalación desde tag.

## Estado de la tarea

- Versión vigente: `0.3.2` en las cuatro fuentes (`pyproject.toml`, `__init__.py`, nombre del wheel, METADATA).
- Último commit: `aea6630` ("feat: add agent hardening and evaluation baseline"). Working tree: limpio. Branch: `main`, up to date con `origin/main`.
- **Entregables de v0.3.2 entregados y commitados:**
  - `tools/ai/verify_opencode.py`: quinto gate, inspecciona plugin, artefactos, headings y sync root↔template. 8 invariantes. Resumen `8/8`.
  - `tools/ai/record_evaluation.py`: registrador manual opt-in sin red. Escritura atómica con `try/finally` que cubre KeyboardInterrupt.
  - `.opencode/commands/compact-test.md`: comando para prueba manual controlada de compactación.
  - `tests/test_verify_opencode.py`: 47 tests herméticos (4 añadidos en esta sesión: `resolve_repo_root`, `wrong_heading_level`, `forbidden_http_module`, `plugin_forbidden_import_network`).
  - `tests/test_record_evaluation.py`: 31 tests herméticos (2 añadidos: limpieza de `.tmp` ante fallo y KeyboardInterrupt).
  - `tests/test_verify_wheel.py` ampliado a 12 recursos obligatorios.
  - `tests/test_new_project.py` ampliado con 7 artefactos OpenCode.
  - ADR-013 documentada en `docs/decisions.md`.
  - `docs/todos.md` actualizado con cadena de cierre.
- **Correcciones aplicadas en esta sesión:**
  - Resumen 8/8 derivado de `TOTAL_OK_CHECKS = 8`.
  - `resolve_repo_root()` pública desde `Path(__file__).resolve().parents[2]`, sin depender de `Path.cwd()`.
  - `append_entry` refactorizado a `try/finally` para limpieza en KeyboardInterrupt y fallos.
  - Falsos positivos del `/review` corregidos en `docs/ai/evaluations.md`.

## Hechos verificados

- `git status --short` → sin cambios (working tree limpio).
- `git diff --stat` → 16 archivos modificados, +416/-72 (desde el commit base).
- `git log --oneline -10` → el último commit `aea6630` es el de v0.3.2.
- `uv run python tools/ai/verify.py` → `OK: los 5 quality gates han pasado.`
  - `ruff check` → All checks passed.
  - `ruff format --check` → 12 files already formatted.
  - `pyright` → 0 errors, 0 warnings, 0 informations.
  - `pytest` → 121 passed.
  - `verify_opencode` → `OK: invariantes verificados (8/8)`.
- `uv run pytest --collect-only -q` → 121 tests collected.
  - tests/test_new_project.py: 35
  - tests/test_record_evaluation.py: 31
  - tests/test_verify_opencode.py: 47
  - tests/test_verify_wheel.py: 8
- `rm -rf dist && uv build` → `python_ai_template-0.3.2-py3-none-any.whl`, `python_ai_template-0.3.2.tar.gz`.
- `uv run python tools/ai/verify_wheel.py` → `OK: wheel verificado correctamente.` 4 fuentes de versión en `0.3.2`, 12 recursos obligatorios presentes.
- `cmp .opencode/.../structured-compaction.ts src/.../template/.../structured-compaction.ts` → plugin idéntico byte a byte.
- `git diff --check` → limpio (sin whitespace problemático).
- No existen secretos, claves, tokens, endpoints privados ni datos personales en ningún archivo de esta unidad.
- `resolve_repo_root()` devuelve la raíz real del repositorio independientemente del `cwd`.

## Decisiones adoptadas

- **ADR-013**: línea base de hardening y evaluación. Agrega quinto gate (`verify_opencode.py`), registrador manual (`record_evaluation.py`), comando `/compact-test`, presupuesto contractual del scout, política canónica de distribución (template como fuente), sync obligatorio root↔template, 12 recursos en el wheel, 4 artefactos OpenCode en el template distribuido. Sin telemetría externa, sin routing adaptativo, sin dependencias de runtime.
- **TOTAL_OK_CHECKS = 8**: el resumen del validador deriva el conteo de una constante única (no duplicada en el mensaje).
- **resolve_repo_root() pública**: la función de resolución de raíz es pública para permitir tests y uso desde fuera del módulo, satisfaciendo pyright strict.
- **try/finally en append_entry**: cubre KeyboardInterrupt y cualquier excepción sin capturar BaseException.
- **No se añadió Cavemem, OpenRouter, Caveman, Ponytail Ultra ni routing adaptativo**: fuera del alcance de v0.3.2.
- **No se añadió telemetría externa, envío de métricas, ni extracción de tokens**: documentado en ADR-013.

## Archivos modificados

Desde el commit base `49dfcde` (v0.3.1), el diff acumulado de v0.3.2 incluye 25 archivos (+3593/-69). Los archivos modificados en esta sesión de correcciones (sobre el commit `d87abbb` intermedio):

| Archivo | Cambio |
|---------|--------|
| `tools/ai/verify_opencode.py` | (creado) +847 líneas. Constante `TOTAL_OK_CHECKS`, función `resolve_repo_root()`, resumen `8/8` |
| `tools/ai/record_evaluation.py` | (creado) +361 líneas. `append_entry` con `try/finally`, limpieza de `.tmp` en KeyboardInterrupt |
| `tests/test_verify_opencode.py` | (creado) +685 líneas. 47 tests incluyendo `resolve_repo_root`, `wrong_heading_level`, `forbidden_http_module` |
| `tests/test_record_evaluation.py` | (creado) +411 líneas. 31 tests incluyendo limpieza de `.tmp` en fallo e interrupción |
| `docs/ai/evaluations.md` | (modificado) Nueva entrada documentando correcciones finales y falsos positivos |
| `pyproject.toml` | (modificado) `version = "0.3.2"`, `extraPaths = ["src", "tools/ai"]` |
| `src/python_ai_template/__init__.py` | (modificado) `__version__ = "0.3.2"` |
| `uv.lock` | (modificado) regenerado: `v0.3.1 -> v0.3.2` |

Los 17 archivos restantes de v0.3.2 (scout, review, handoff, verify, compact-test, structured-compaction.ts, SKILL.md, AGENTS.md, docs/architecture.md, docs/decisions.md, docs/todos.md, docs/ai/context-policy.md, tests/test_new_project.py, tests/test_verify_wheel.py, tools/ai/verify.py, tools/ai/verify_wheel.py) fueron entregados y commitados en `aea6630`.

No se modificaron: `src/python_ai_template/generator.py`, `tools/new_project.py`, `.github/workflows/ci.yml`, `README.md`, `docs/glossary.md`, `docs/mistakes.md`.

## Validaciones ejecutadas

### Gates locales (ejecutados en esta sesión)

| Gate | Comando | Resultado |
|------|---------|-----------|
| ruff check | `uv run ruff check .` | All checks passed |
| ruff format --check | `uv run ruff format --check .` | 12 files already formatted |
| pyright | `uv run pyright` | 0 errors, 0 warnings, 0 informations |
| pytest | `uv run pytest` | 121 passed |
| verify_opencode | `uv run python tools/ai/verify_opencode.py` | OK: invariantes verificados (8/8) |
| orquestador completo | `uv run python tools/ai/verify.py` | OK: los 5 quality gates han pasado |

### Wheel

| Comando | Resultado |
|---------|-----------|
| `rm -rf dist && uv build` | `python_ai_template-0.3.2-py3-none-any.whl`, `python_ai_template-0.3.2.tar.gz` |
| `uv run python tools/ai/verify_wheel.py` | OK: 4 fuentes coinciden en 0.3.2, 12 recursos presentes |
| `cmp` plugin root↔template | byte a byte idéntico |

### Inventario Git

| Comando | Resultado |
|---------|-----------|
| `git status --short` | sin cambios, working tree limpio |
| `git diff --stat` | 16 archivos, +416/-72 (v0.3.2 completo) |
| `git diff --check` | limpio |
| `git log --oneline -10` | último commit `aea6630` v0.3.2 |

### No ejecutados en esta sesión

- CI remota (GitHub Actions): el commit `aea6630` está en `main` local pero no se ha hecho push a `origin/main`.
- Tag `v0.3.2`: no creado.
- Instalación desde tag: no ejecutada (depende del tag).
- Compactación real disparada por OpenCode: sigue pendiente (no ha cambiado desde v0.3.1).
- `/compact-test`: no ejecutado en esta sesión.

## Errores pendientes

- **Ninguno bloqueante.** Los cinco quality gates pasan localmente. No hay regresiones.
- **Carácter experimental del hook** `experimental.session.compacting` en OpenCode 1.18.4: no ha cambiado desde v0.3.1. Si una versión futura renombra el hook o cambia su firma, el plugin dejará de registrar el callback de forma silenciosa. ADR-012 lo documenta.
- **Validación del plugin en sesión interactiva larga**: la compactación real por umbral no se ha disparado en ninguna sesión. Pendiente desde v0.3.1.

## Enfoques rechazados y motivo

- **Leer `docs/current-state.md` desde el plugin**: rechazado por "no usa filesystem". El plugin es estático (ADR-012).
- **Automatizar `/review` mediante hooks**: rechazado porque OpenCode 1.18.4 solo expone `command.execute.before`, no `after`.
- **Usar `tsc`/`npx`/toolchain temporal**: rechazado por el principio de cambio mínimo en la cadena de herramientas.
- **Cavemem, OpenRouter, routing adaptativo, telemetría externa**: rechazados en v0.3.2; fuera del alcance (ADR-013).
- **Persistir resumen de compactación en disco desde el plugin**: rechazado (ADR-012).
- **Reemplazar `output.prompt`**: rechazado (ADR-012: el plugin es auxiliar, no autoridad).
- **`Path.cwd()` como raíz implícita en el validador**: rechazado y corregido por `resolve_repo_root()` desde `__file__`.
- **`except Exception` en `append_entry`**: rechazado y reemplazado por `try/finally` para cubrir KeyboardInterrupt.

## Divergencias detectadas

- **Ninguna** al cierre de esta sesión. El código commitado refleja el estado documentado en `docs/`, y los gates confirman coherencia.

## Siguiente acción concreta

Cuando el usuario lo autorice, hacer push de `main` a `origin/main` para disparar CI remota; si CI pasa, crear el tag `v0.3.2` (`git tag v0.3.2 && git push origin v0.3.2`); instalar localmente con `uv tool install .` y validar que `new-python-project --version` devuelve `0.3.2`. Luego mover v0.3.2 de "En revisión" a "Completadas recientemente → Cerrada" en `docs/todos.md`.
