# Estado actual

Estado del repositorio tras el cierre de v0.3.2. Este archivo se reescribe con `/handoff` al final de cada bloque de trabajo siguiendo el formato canónico definido en la skill `context-handoff`. Permite retomar el trabajo sin la conversación previa.

## Objetivo actual

v0.3.2 cerrada. Hardening de agentes y línea base de evaluación (ADR-013) publicado: CI remota aprobada (run `30058735050`), tag `v0.3.2` publicado, instalación desde tag validada. Planificar la unidad posterior sin implementar Cavemem.

## Estado de la tarea

- **v0.3.2**: cerrada.
- Versión publicada: `0.3.2` en las cuatro fuentes (`pyproject.toml`, `__init__.py`, nombre del wheel, METADATA).
- Commit funcional: `aea6630` ("feat: add agent hardening and evaluation baseline").
- Commit de release: `f063fe2` ("chore: release python-ai-template 0.3.2").
- Tag remoto: `v0.3.2` apunta a `f063fe2`.
- CI final: run `30058735050` — jobs `quality` (Python 3.12 y 3.14) y `package` aprobados.
- Instalación desde tag: validada. `new-python-project --version` devolvió `0.3.2`. `new-python-project --help` funcionó. Proyecto temporal generado correctamente.
- Los siete artefactos OpenCode distribuidos quedaron presentes en el proyecto generado.
- Herramienta desinstalada correctamente tras la validación.
- Working tree: limpio. Branch: `main`, up to date con `origin/main`.

## Hechos verificados

- `git log --oneline -10` incluye `f063fe2` (release) y `aea6630` (feat).
- `git status --short` → sin cambios.
- Tag `v0.3.2` existe en remoto y apunta a `f063fe2`.
- CI run `30058735050`: jobs `quality` 3.12, `quality` 3.14 y `package` aprobados.
- `uv tool install ...` desde el tag remoto: exitoso.
- `new-python-project --version` → `0.3.2`.
- `new-python-project --help` → ayuda impresa sin errores.
- Proyecto temporal generado contenía los 7 artefactos OpenCode distribuidos.
- `uv tool uninstall python-ai-template`: exitoso.
- No existen secretos, claves, tokens, endpoints privados ni datos personales en ningún archivo de esta unidad.

## Decisiones adoptadas

- **ADR-013** (v0.3.2): hardening de agentes y línea base de evaluación. Cerrada y publicada.
- **ADR-012** (v0.3.1): capa de exploración y compactación. Cerrada en release anterior.
- **ADR-011** (v0.3.0): CI reproducible. Cerrada en release anterior.

## Archivos modificados

Working tree limpio. Ningún cambio sin commitear respecto al tag `v0.3.2`.

## Validaciones ejecutadas

### CI remota (run `30058735050`)

| Job | Estado |
|-----|--------|
| `quality` (Python 3.12) | aprobado |
| `quality` (Python 3.14) | aprobado |
| `package` | aprobado |

### Validación local desde tag remoto

| Comando | Resultado |
|---------|-----------|
| `uv tool install python-ai-template --from https://github.com/...` | exitoso |
| `new-python-project --version` | `0.3.2` |
| `new-python-project --help` | ayuda impresa |
| proyecto generado: 7 artefactos OpenCode | presentes |
| `uv tool uninstall python-ai-template` | exitoso |

### Gates locales (última ejecución conocida, working tree limpio)

| Gate | Resultado |
|------|-----------|
| `ruff check` | All checks passed |
| `ruff format --check` | 12 files already formatted |
| `pyright` | 0 errors, 0 warnings, 0 informations |
| `pytest` | 121 passed |
| `verify_opencode` | OK: invariantes verificados (8/8) |
| `uv build && verify_wheel.py` | OK: 0.3.2, 12 recursos |

### No ejecutados en esta sesión

- Compactación real disparada por OpenCode por umbral: experimental, pendiente desde v0.3.1. No se ha provocado en ninguna sesión.

## Errores pendientes

- **Ninguno bloqueante.** v0.3.2 cerrada sin regresiones.
- **Carácter experimental del hook** `experimental.session.compacting`: riesgo conocido desde ADR-012. El plugin puede dejar de registrar el callback si OpenCode renombra o elimina el hook experimental.
- **Compactación real por umbral**: no se ha disparado ni verificado empíricamente en ninguna sesión. Sigue siendo el riesgo abierto principal del plugin.

## Enfoques rechazados y motivo

- (ninguno nuevo en esta sesión de cierre; los enfoques rechazados de v0.3.1 y v0.3.2 están documentados en handoffs anteriores).

## Divergencias detectadas

- **Ninguna.** El código commitado, el tag publicado y la documentación están alineados.

## Siguiente acción concreta

Planificar la unidad posterior a v0.3.2. No implementar Cavemem, OpenRouter, routing adaptativo ni telemetría externa sin una ADR propia. Considerar si la próxima unidad aborda la compactación experimental, la automatización parcial de `/compact-test`, o tareas de mantenimiento del backlog.
