# Estado actual

Estado del repositorio tras el cierre de v0.3.3. Este archivo se reescribe con `/handoff` al final de cada bloque de trabajo siguiendo el formato canónico definido en la skill `context-handoff`. Permite retomar el trabajo sin la conversación previa.

## Objetivo actual

v0.3.3 cerrada funcionalmente y validada desde el tag remoto. Mantener el plugin `structured-compaction` en estado experimental (ADR-014) y limitar el alcance del release: no introducir telemetría, persistencia, red, base de datos ni dependencias runtime; no promover el plugin a mecanismo validado por ausencia de evidencia empírica.

## Estado de la tarea

- **v0.3.3**: release cerrada.
- Versión vigente: `0.3.3` en las cuatro fuentes (`pyproject.toml`, `__init__.py`, nombre del wheel, METADATA).
- Commit funcional: `60697ce` ("feat: validate structured compaction workflow").
- Commit documental de release: `29ae680` ("docs: record v0.3.3 release readiness").
- Tag remoto: `v0.3.3` apunta a `29ae680`.
- Instalación desde tag: validada. `python-ai-template==0.3.3` instalado desde el tag remoto.
- `new-python-project --version`: `0.3.3`.
- `new-python-project --help`: ayuda impresa sin errores.
- Proyecto temporal: generado correctamente. Los 9 artefactos OpenCode objetivo presentes en el proyecto generado.
- Herramienta: desinstalada correctamente. Directorio temporal eliminado.
- Working tree antes del cambio documental actual: limpio. Branch: `main`, al día con `origin/main` antes del cambio documental actual.

### CI remota aprobaba

- Primera CI `30139073129`: jobs `quality` (Python 3.12), `quality` (Python 3.14) y `package` aprobados.
- Segunda CI `30139219673`: jobs `quality` (Python 3.12), `quality` (Python 3.14) y `package` aprobados tras el commit documental de release.

### Pasos de release completados en v0.3.3

- Bump `0.3.2` → `0.3.3` en `pyproject.toml` y `src/python_ai_template/__init__.py`.
- `uv lock` regenerado; diff mecánico en `uv.lock`.
- Gates locales verdes: `ruff check`, `ruff format --check`, `pyright` (0 errors), `pytest` (145 passed), `verify_opencode` (8/8).
- `rm -rf dist && uv build && uv run python tools/ai/verify_wheel.py`: wheel `python_ai_template-0.3.3-py3-none-any.whl` con 14/14 recursos obligatorios.
- Commit funcional `60697ce` creado y pusheado a `main`.
- Primera CI remota `30139073129` aprobada (3 jobs en verde).
- Commit documental de release `29ae680` creado y pusheado a `main`.
- Segunda CI remota `30139219673` aprobada (3 jobs en verde).
- Tag `v0.3.3` publicado apuntando a `29ae680`.
- Instalación desde tag remoto validada: `python-ai-template==0.3.3`.
- `new-python-project --version` devolvió `0.3.3`.
- `new-python-project --help` validado.
- Proyecto temporal generado correctamente con los 9 artefactos OpenCode objetivo.
- Herramienta desinstalada; directorio temporal eliminado.

### Pendiente únicamente el cierre documental post-tag

- Commit documental posterior al tag (`docs/todos.md`, `docs/current-state.md`, `docs/ai/evaluations.md`).
- Push.
- CI final con el árbol limpio.
- Verificar working tree limpio.

## Hechos verificados

- `git status --short` antes del cambio documental actual: vacío.
- `git log` incluye los commits `60697ce` (funcional) y `29ae680` (documental de release).
- Tag `v0.3.3` existe en remoto y apunta a `29ae680`.
- CI run `30139073129`: jobs `quality` 3.12, `quality` 3.14 y `package` aprobados.
- CI run `30139219673`: jobs `quality` 3.12, `quality` 3.14 y `package` aprobados.
- `uv tool install python-ai-template==0.3.3` desde el tag remoto: exitoso.
- `new-python-project --version` → `0.3.3`.
- `new-python-project --help` → ayuda impresa sin errores.
- Proyecto temporal generado contenía los 9 artefactos OpenCode objetivo (los 7 previos + los 2 fixtures).
- `uv tool uninstall python-ai-template`: exitoso.
- Directorio temporal del proyecto generado: eliminado.
- No existen secretos, claves, tokens, endpoints privados ni datos personales en ningún archivo de esta unidad.

### Artefactos OpenCode objetivo validados en el proyecto generado

- `.opencode/agents/scout.md`.
- `.opencode/commands/review.md`.
- `.opencode/commands/handoff.md`.
- `.opencode/commands/verify.md`.
- `.opencode/commands/compact-test.md`.
- `.opencode/skills/context-handoff/SKILL.md`.
- `.opencode/plugins/structured-compaction.ts`.
- `.opencode/fixtures/compaction-checkpoint.md`.
- `.opencode/fixtures/compaction-filler.md`.

### Gaps de observación declarados (evidencia histórica)

- Las dos corridas controladas de `/compact-test` (MiniMax-M3/minimax-direct y gpt-5.6-sol/openai) fueron `inconclusive` por agotamiento de presupuesto sin compactación nativa confirmada.
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
- `docs/ai/compaction-evaluation.md`: informe comparativo con tabla de MiniMax/Codex y conclusión final.
- `docs/ai/evaluations.md`: dos entradas nuevas (corridas `inconclusive` MiniMax y Codex).
- `docs/decisions.md`: ADR-014 anexada al registro único.
- `pyproject.toml` y `src/python_ai_template/__init__.py`: bump `0.3.2` → `0.3.3`.
- `uv.lock`: regenerado por `uv lock`.

### Cambios de v0.3.3 commiteados en `29ae680` (documental de release)

- `docs/todos.md`: bloque v0.3.3 actualizado con bump, gates, build, primera CI y siguientes pasos pendientes.
- `docs/current-state.md`: estado operativo v0.3.3 con primera CI aprobada.

### Cambios pendientes sin commitear (este cambio)

- `docs/todos.md`: marcar v0.3.3 como release cerrada y reducir pendientes al cierre documental post-tag.
- `docs/current-state.md`: reflejar cierre funcional y validación desde el tag remoto.
- `docs/ai/evaluations.md`: entrada única de validación post-tag de v0.3.3.

## Validaciones ejecutadas

### CI remota `30139073129` (primera)

| Job | Estado |
|-----|--------|
| `quality` (Python 3.12) | aprobado |
| `quality` (Python 3.14) | aprobado |
| `package` | aprobado |

### CI remota `30139219673` (segunda)

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

### Validación desde el tag remoto `v0.3.3`

| Comando | Resultado |
|---------|-----------|
| Tag remoto `v0.3.3` apuntando a `29ae680` | publicado |
| `uv tool install python-ai-template==0.3.3` desde tag | exitoso |
| `new-python-project --version` | `0.3.3` |
| `new-python-project --help` | ayuda impresa |
| Proyecto generado: 9 artefactos OpenCode | presentes |
| `uv tool uninstall python-ai-template` | exitoso |
| Directorio temporal del proyecto | eliminado |

### Pendiente al cierre del release

- CI final con el árbol limpio tras este cambio documental.

## Errores pendientes

- **Ninguno bloqueante.** v0.3.3 cerrada sin regresiones.
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

- **Ninguna en el release cerrado.** El código commiteado, el push, ambas CI remotas, el tag remoto, la instalación validada, el proyecto generado con 9 artefactos y la documentación están alineados en `v0.3.3`.
- La única divergencia operativa es que el cambio documental actual (`docs/todos.md`, `docs/current-state.md`, `docs/ai/evaluations.md`) aún no se ha commiteado tras la validación desde el tag remoto; ese commit forma parte del flujo de release pendiente y se describe en el bloque "Pendiente únicamente el cierre documental post-tag".

## Siguiente acción concreta

Realizar el commit documental posterior al tag con `docs/todos.md`, `docs/current-state.md` y `docs/ai/evaluations.md`, hacer push, correr la CI final y verificar el working tree limpio. No introducir Cavemem, OpenRouter, routing adaptativo ni telemetría externa sin una ADR propia.
