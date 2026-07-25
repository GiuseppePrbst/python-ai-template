# Estado actual

Estado del repositorio durante el release de v0.3.3. Este archivo se reescribe con `/handoff` al final de cada bloque de trabajo siguiendo el formato canónico definido en la skill `context-handoff`. Permite retomar el trabajo sin la conversación previa.

## Objetivo actual

Cerrar la release de v0.3.3 — capa de compactación experimental con fixtures sintéticos distribuidos, validación estática ampliada y ADR-014 aceptado. Mantener el plugin `structured-compaction` en estado experimental y limitar el alcance del release: no introducir telemetría, persistencia, red, base de datos ni dependencias runtime; no promover el plugin a mecanismo validado por ausencia de evidencia empírica.

## Estado de la tarea

- **v0.3.3**: implementación y evidencia completas; revisión documental completa; ADR-014 aceptado; bump, build y primera CI completados; release pendiente.
- Versión vigente: `0.3.3` en las cuatro fuentes (`pyproject.toml`, `__init__.py`, nombre del wheel, METADATA).
- Commit funcional: `60697ce` ("feat: validate structured compaction workflow").
- Push: `main` actualizado en `origin/main`.
- Primera CI remota: run `30139073129` — jobs `quality` (Python 3.12), `quality` (Python 3.14) y `package` aprobados.
- Tag remoto: pendiente. No se afirma que el tag `v0.3.3` exista todavía.
- Instalación desde tag: pendiente.
- Working tree: cambios documentales en curso (`docs/todos.md`, `docs/current-state.md`) sin commitear. Branch: `main`, al día con `origin/main` antes del commit documental de release.

### Pasos de release completados en v0.3.3

- Bump `0.3.2` → `0.3.3` en `pyproject.toml` y `src/python_ai_template/__init__.py`.
- `uv lock` regenerado; diff mecánico en `uv.lock`.
- Gates locales verdes: `ruff check`, `ruff format --check`, `pyright` (0 errors), `pytest` (145 passed), `verify_opencode` (8/8).
- `rm -rf dist && uv build && uv run python tools/ai/verify_wheel.py`: wheel `python_ai_template-0.3.3-py3-none-any.whl` con 14/14 recursos obligatorios.
- Commit funcional `60697ce` creado y pusheado a `main`.
- Primera CI remota `30139073129` aprobada (3 jobs en verde).

### Pasos de release pendientes en v0.3.3

- Commit documental de release (este cambio) sobre `docs/todos.md` y `docs/current-state.md`.
- Segunda CI tras el commit documental.
- Tag `v0.3.3` apuntando al commit de release.
- Instalación desde tag remoto validada.
- Generación de proyecto temporal con 9 artefactos OpenCode (los 7 previos + los 2 fixtures).
- Documentación posterior al tag (anotación del cierre y de la instalación validada).
- CI final con el árbol limpio.
- Working tree limpio.

## Hechos verificados

- `git status --short` antes del commit funcional mostraba los cambios de v0.3.3 sin commits pendientes en el cuerpo del release.
- `uv run python tools/ai/verify.py` ejecutado localmente: 5 gates en verde, `pytest` 145 passed, `verify_opencode` 8/8.
- `uv build && uv run python tools/ai/verify_wheel.py`: cuatro fuentes de versión coinciden en `0.3.3`; wheel `python_ai_template-0.3.3-py3-none-any.whl` con 14/14 recursos obligatorios.
- Primera CI remota `30139073129`: jobs `quality` 3.12, `quality` 3.14 y `package` aprobados.
- `git log` incluye el commit funcional `60697ce` con mensaje "feat: validate structured compaction workflow".
- Branch `main` al día con `origin/main` tras el push del commit funcional.

### Gaps de observación declarados

- No se ha confirmado compactación nativa en ninguna sesión.
- No existe resumen post-compactación observado.
- La retención de los 11 marcadores, los 10 headings canónicos y `NEXT-01` no es evaluable sin resumen.
- La causalidad del plugin no es observable directamente porque el plugin no produce logs ni telemetría.
- El plugin sigue siendo experimental; ADR-014 formaliza este estado.

## Decisiones adoptadas

- **ADR-014** (v0.3.3): mantener la compactación estructurada en estado experimental. Aceptada y archivada en `docs/decisions.md`. No promover el plugin a mecanismo validado, no eliminarlo por ausencia de evidencia de fallo, no ampliar su funcionalidad, no añadir telemetría, persistencia, red, base de datos ni dependencias runtime.
- **ADR-013** (v0.3.2): validación estática de OpenCode y línea base de evaluación. Vigente.
- **ADR-012** (v0.3.1): capa de exploración y compactación estructurada. Vigente.

## Archivos modificados

### Cambios de v0.3.3 commiteados en `60697ce`

- `.opencode/commands/compact-test.md` y copia canónica en `src/python_ai_template/template/.opencode/commands/compact-test.md`: comando actualizado con protocolo acotado, distinción marcador literal/contenido semántico y rúbrica de cinco niveles.
- `tools/ai/verify_opencode.py`: `SYNC_PAIRS` pasa de 7 a 9 pares (incorpora los dos fixtures).
- `tools/ai/verify_wheel.py`: `REQUIRED_RESOURCES` pasa de 12 a 14 entradas (incorpora los dos fixtures).
- `tests/test_compaction_fixture.py`: 11 tests herméticos nuevos sobre los fixtures (heading order, marcadores únicos, ausencia de secretos, URLs, rutas personales y referencias al proyecto real; sync root↔template).
- `tests/test_verify_opencode.py`: 6 tests nuevos sobre sync de fixtures.
- `tests/test_new_project.py`: 3 tests E2E nuevos sobre presencia e identidad de los fixtures en el proyecto generado.
- `tests/test_verify_wheel.py`: 5 tests nuevos sobre `REQUIRED_RESOURCES` actualizado.
- `.opencode/fixtures/compaction-checkpoint.md` y `.opencode/fixtures/compaction-filler.md` y copias en `src/python_ai_template/template/.opencode/fixtures/`: fixtures sintéticos nuevos.
- `docs/architecture.md`: nota sobre fixtures y `/compact-test`.
- `docs/todos.md` y `docs/current-state.md`: documentación de release en este commit (cambio actual).
- `docs/ai/compaction-evaluation.md`, `docs/ai/evaluations.md`, `docs/decisions.md`: informe comparativo, entradas de evaluación y ADR-014.
- `pyproject.toml` y `src/python_ai_template/__init__.py`: bump `0.3.2` → `0.3.3`.
- `uv.lock`: regenerado por `uv lock`.

### Cambios pendientes sin commitear

- `docs/todos.md` y `docs/current-state.md`: actualización de release post-CI (este cambio).

## Validaciones ejecutadas

### CI remota (run `30139073129`)

| Job | Estado |
|-----|--------|
| `quality` (Python 3.12) | aprobado |
| `quality` (Python 3.14) | aprobado |
| `package` | aprobado |

### Gates locales antes del commit funcional

| Gate | Resultado |
|------|-----------|
| `ruff check` | All checks passed |
| `ruff format --check` | 13 files already formatted |
| `pyright` | 0 errors, 0 warnings, 0 informations |
| `pytest` | 145 passed |
| `verify_opencode` | OK: invariantes verificados (8/8) |
| `uv build && verify_wheel.py` | OK: 0.3.3, 14/14 recursos |

### Validación local desde el wheel `0.3.3`

| Recurso | Presente |
|---------|----------|
| `python_ai_template/template/.gitignore` | sí |
| `python_ai_template/template/.opencode/.gitignore` | sí |
| `python_ai_template/template/pyproject.toml.tmpl` | sí |
| `python_ai_template/template/src/__package_name__/__init__.py.tmpl` | sí |
| `python_ai_template/template/tests/test_smoke.py.tmpl` | sí |
| `python_ai_template/template/.opencode/agents/scout.md` | sí |
| `python_ai_template/template/.opencode/commands/review.md` | sí |
| `python_ai_template/template/.opencode/commands/handoff.md` | sí |
| `python_ai_template/template/.opencode/commands/verify.md` | sí |
| `python_ai_template/template/.opencode/commands/compact-test.md` | sí |
| `python_ai_template/template/.opencode/skills/context-handoff/SKILL.md` | sí |
| `python_ai_template/template/.opencode/plugins/structured-compaction.ts` | sí |
| `python_ai_template/template/.opencode/fixtures/compaction-checkpoint.md` | sí |
| `python_ai_template/template/.opencode/fixtures/compaction-filler.md` | sí |

### Pendientes en este release

- Segunda CI tras el commit documental.
- Tag `v0.3.3` y validación de instalación desde tag.
- Generación de proyecto temporal con 9 artefactos OpenCode.
- Documentación posterior al tag.
- CI final con árbol limpio.

## Errores pendientes

- **Ninguno bloqueante.** v0.3.3 sigue sin regresiones.
- **Carácter experimental del hook** `experimental.session.compacting`: riesgo conocido desde ADR-012, reafirmado por ADR-014. El plugin puede dejar de registrar el callback si OpenCode renombra o elimina el hook experimental.
- **Compactación real por umbral**: no se ha disparado ni verificado empíricamente en ninguna sesión. Las dos corridas controladas de `/compact-test` (MiniMax y Codex) fueron `inconclusive` por agotamiento de presupuesto sin compactación confirmada. Sigue siendo el riesgo abierto principal del plugin.
- **Causalidad del plugin no observable**: sin logs ni telemetría, no es posible atribuir causalidad al plugin. ADR-014 mantiene el plugin en estado experimental por este motivo.

## Enfoques rechazados y motivo

- **Promover el plugin a mecanismo validado**: rechazado en ADR-014 por falta de evidencia empírica.
- **Eliminar el plugin**: rechazado en ADR-014 por ausencia de evidencia de fallo atribuible.
- **Añadir instrumentación** (logs, contadores, eventos o almacenamiento local) para forzar observación: rechazado en ADR-014 por ampliar el alcance de v0.3.3 y por contradecir ADR-013 (sin telemetría, sin dependencias runtime, sin medición de tokens).
- **Repetir corridas idénticas del comando `/compact-test` sólo para generar más filler**: rechazado en ADR-014. Futuras pruebas requieren una señal observable de compactación o una configuración materialmente distinta.
- (Los enfoques rechazados de v0.3.1 y v0.3.2 están documentados en handoffs anteriores y en ADR-012, ADR-013.)

## Divergencias detectadas

- **Ninguna.** El código commiteado, el push, la primera CI remota y la documentación están alineados en `0.3.3`. El tag remoto no existe todavía; eso es esperado en este punto del release.
- La única divergencia operativa es que `docs/todos.md` y `docs/current-state.md` aún no están commiteados tras la primera CI; ese commit forma parte del flujo de release pendiente y se describe en el bloque "Pasos de release pendientes".

## Siguiente acción concreta

Continuar el release de v0.3.3 con el commit documental sobre `docs/todos.md` y `docs/current-state.md`, esperar la segunda CI, crear el tag `v0.3.3`, validar la instalación desde el tag remoto y generar un proyecto temporal con 9 artefactos OpenCode (los 7 previos + los 2 fixtures). Tras la instalación validada y la documentación posterior al tag, correr la CI final y dejar el working tree limpio. No introducir Cavemem, OpenRouter, routing adaptativo ni telemetría externa sin una ADR propia.
