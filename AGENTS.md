# AGENTS.md

Convenciones operativas para cualquier agente — humano o IA — que trabaje en este repositorio.

Este archivo es la fuente de verdad operativa. La documentación detallada vive en `docs/` y se referencia aquí por tarea. No dupliques en `AGENTS.md` el contenido que ya existe en `docs/`.

## Reglas obligatorias

1. **El repositorio es la fuente de verdad.** El código, la configuración vigente y `docs/` prevalecen sobre cualquier resumen externo o memoria del modelo.
2. **Prohibido introducir secretos** (claves, tokens, contraseñas, endpoints privados, identificadores internos, datos personales) en código, configuración, ejemplos, fixtures, tests, logs, commits ni documentación. Si se necesita una credencial, se obtiene por variable de entorno y nunca se almacena en el repo.
3. **Plan antes de cambios amplios.** Cualquier cambio que afecte a más de un módulo, a la arquitectura, a la configuración de herramientas, a la documentación estructural o a la API pública requiere un plan breve aprobado por el usuario antes de empezar a editar.
4. **Cambios pequeños y revisables.** Cada bloque de cambios debe ser acotado, fácil de revisar y reversible. Evita diffs que mezclen refactors, formato, lógica y documentación sin justificación.
5. **No commits sin autorización explícita.** Los agentes no hacen commits. Solo commitea el usuario o alguien con permiso explícito.
6. **Validaciones antes de "terminado".** Nada se considera terminado sin pasar los quality gates obligatorios definidos abajo.
7. **Prohibido ocultar errores ni relajar controles** (desactivar reglas, ampliar ignores, añadir `noqa` o `type: ignore`, relajar tipos, saltarse o borrar tests) para que las validaciones pasen. Si una validación falla, se corrige la causa.
8. **Causa raíz antes que workaround.** Antes de introducir un atajo, se investiga la causa raíz del fallo. Si un workaround es inevitable, se documenta y se propone una entrada en `docs/decisions.md`.

## Quality gates obligatorios

Ejecutar, desde la raíz del repositorio y en este orden:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

El atajo canónico es `uv run python tools/ai/verify.py`, que invoca los
cuatro comandos en el mismo orden con `subprocess.run`, se detiene al
primer fallo y propaga su `exit code`. El contrato es idéntico en local
y en CI (`.github/workflows/ci.yml`).

Si alguno falla, el cambio **no** está terminado. Para cambios únicamente de documentación, basta con que los quality gates existentes continúen pasando sin nuevas regresiones.

## Definición de terminado

Un cambio se considera terminado solo si se cumplen **todas** estas condiciones:

1. El código compila o puede importarse sin errores.
2. `uv run ruff check .` pasa.
3. `uv run ruff format --check .` pasa.
4. `uv run pyright` pasa.
5. `uv run pytest` pasa.
6. El diff fue revisado por el autor antes de declararlo cerrado.
7. La documentación afectada está actualizada (`docs/`, `README.md` si aplica, docstrings).
8. No hay secretos, logs temporales ni archivos generados no deseados en el árbol de trabajo.
9. No se realizaron commits sin autorización explícita.

## Mapa de documentos por tarea

| Tarea | Documentos a leer (en este orden) |
|-------|------------------------------------|
| Empezar o retomar una sesión | `docs/current-state.md`, `docs/todos.md` |
| Implementar funcionalidad | `docs/architecture.md`, `docs/decisions.md`, `docs/glossary.md`, skill `python-quality` |
| Revisar un cambio | `docs/architecture.md`, `docs/decisions.md`, agente `reviewer` |
| Diagnosticar un fallo | `docs/architecture.md`, `docs/mistakes.md`, agente `debugger`, skill `python-quality` |
| Modificar arquitectura o límites | `docs/architecture.md`, `docs/decisions.md`, skill `architecture-review`, agente `implementer` (con plan aprobado) |
| Registrar una decisión | `docs/decisions.md`, comando `/decision` |
| Registrar un error recurrente | `docs/mistakes.md`, comando `/mistake` |
| Pasar el relevo a otra sesión | `docs/current-state.md`, comando `/handoff` |
| Elegir o evaluar modelo | `docs/ai/model-policy.md`, `docs/ai/evaluations.md` |
| Gestionar contexto | `docs/ai/context-policy.md` |

## Roles disponibles (`.opencode/agents/`)

- `implementer`: implementación cotidiana sobre un plan aprobado.
- `reviewer`: revisión sin modificar archivos salvo instrucción explícita.
- `debugger`: diagnóstico con énfasis en causa raíz.
- `documenter`: documentación mínima y útil, basada en código y decisiones vigentes.

## Comandos disponibles (`.opencode/commands/`)

- `/verify`: ejecuta `uv run python tools/ai/verify.py` (los cuatro quality gates).
- `/handoff`: deja `docs/current-state.md` listo para retomar.
- `/decision`: registra una entrada en `docs/decisions.md`.
- `/mistake`: registra un error recurrente en `docs/mistakes.md`.

## Skills disponibles (`.opencode/skills/`)

- `python-quality`: uso correcto de `uv`, `ruff`, `pyright` y `pytest`.
- `architecture-review`: revisión de límites, acoplamiento, reversibilidad y riesgos.

## Privacidad y secretos

- Nunca incluir claves, tokens, contraseñas, endpoints privados ni datos personales en código, configuración, ejemplos, fixtures, tests ni documentación.
- Si se necesita una clave para desarrollo local, documentar únicamente el **nombre** de la variable de entorno esperada (por ejemplo `MINIMAX_API_KEY`), nunca su valor.
- Las configuraciones de OpenCode y de los modelos nunca deben almacenar API keys: siempre se leen del entorno del sistema.
