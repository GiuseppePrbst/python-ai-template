# Estado actual

Estado del repositorio al cierre de esta sesión. Este archivo se reescribe con `/handoff` al final de cada bloque de trabajo siguiendo el formato canónico definido en la skill `context-handoff` (`.opencode/skills/context-handoff/SKILL.md`). Debe permitir retomar el trabajo sin la conversación previa.

## Objetivo actual

Incorporar una capa de exploración y compactación (agente `scout`, comando `/review`, skill `context-handoff`, plugin `structured-compaction`) sin modificar el comportamiento del generador ni introducir dependencias de runtime (v0.3.1). Tras la primera revisión, corregir el plugin para que sea una entrada estrictamente estática añadida a `output.context`, sin filesystem, sin shell, sin red, sin logs y sin persistencia.

## Estado de la tarea

- Versión vigente: `0.3.1` (bump desde `0.3.0`). Cambio aplicado en `pyproject.toml:7` y reflejado por `uv` en `uv.lock:90`.
- Plugin `structured-compaction.ts` reescrito como entrada estática: importa únicamente el tipo `Plugin` desde `@opencode-ai/plugin` 1.18.4, registra `experimental.session.compacting` y empuja una sola cadena literal a `output.context`. Sin `node:fs`, `node:fs/promises`, `node:path`, shell, red, logs ni persistencia. Verificado por `grep -nE "node:fs|node:path|readFile|writeFile|readdir|stat\(" .opencode/plugins/structured-compaction.ts` (cero coincidencias).
- Plugin autodescubierto por OpenCode 1.18.4 desde `.opencode/plugins/`. Confirmado en `opencode debug config`: aparece en `plugin_origins` con `scope: "local"`. `opencode.jsonc` no se modificó.
- Sesión real de OpenCode ejecutada con `opencode run --print-logs --log-level INFO --format json`; sin errores de carga del plugin.
- Quality gates locales en verde con `uv run python tools/ai/verify.py` (33 tests passed, 0 errors, 0 warnings).
- Wheel verificado con `rm -rf dist && uv build && uv run python tools/ai/verify_wheel.py`: las cuatro fuentes de la versión (`pyproject.toml`, `__init__.py`, nombre del wheel, `METADATA Version`) coinciden en `0.3.1`, y los cinco recursos obligatorios de la plantilla están presentes.
- Documentación: `docs/architecture.md` (sección "Capa de exploración y compactación"), `docs/ai/context-policy.md` (política de compactación y handoff alineada con la skill), ADR-012 actualizada en `docs/decisions.md` para reflejar el plugin estático, `docs/todos.md` actualizado, `/review` ampliado para verificar expresamente que los plugins de compactación no usen filesystem.
- Resto de archivos modificados solo en la superficie: `AGENTS.md`, `.opencode/commands/handoff.md`, `.opencode/skills/context-handoff/SKILL.md`, `docs/ai/evaluations.md`. Todos los documentos que antes afirmaban que el plugin leía `docs/current-state.md` o `pyproject.toml` se han corregido para describir el plugin como entrada estática.

## Hechos verificados

- `opencode --version` -> `1.18.4`.
- `opencode debug config` lista el plugin con `"plugin_origins": [{"spec": "file:///.../structured-compaction.ts", "source": "/home/giuseppe/.../.opencode", "scope": "local"}]`.
- `opencode run --print-logs --log-level INFO --format json` confirmó que el plugin se carga sin errores durante la ejecución de una sesión real.
- `grep -nE "node:fs|node:path|readFile|writeFile|readdir|stat\(" .opencode/plugins/structured-compaction.ts` -> cero coincidencias.
- `grep -c "output.context.push" .opencode/plugins/structured-compaction.ts` -> `1`.
- `grep '^## ' docs/current-state.md` -> los diez encabezados canónicos literales.
- `uv run python tools/ai/verify.py` -> `OK: los 4 quality gates han pasado.`
- `uv build` -> produce `dist/python_ai_template-0.3.1-py3-none-any.whl` y `dist/python_ai_template-0.3.1.tar.gz`.
- `uv run python tools/ai/verify_wheel.py` -> `OK: wheel verificado correctamente.` (cuatro fuentes de versión coinciden; cinco recursos obligatorios presentes).
- No existen secretos, claves, tokens, endpoints privados ni datos personales en ningún archivo de esta unidad. Verificación por inspección directa del plugin, de los documentos y de los nuevos recursos.
- No se han modificado `src/python_ai_template/` (más allá del bump de `__version__`), `tests/`, `tools/new_project.py`, ni los archivos de la plantilla. El comportamiento del generador es idéntico al de v0.3.0.

## Decisiones adoptadas

- **ADR-012** actualizada: capa de exploración y compactación para continuidad operativa (v0.3.1). Tras la primera revisión, el plugin pasa a ser una entrada estrictamente estática: sin filesystem, sin shell, sin red, sin logs, sin persistencia. ADR-012 deja claro que el plugin no lee ni escribe archivos, no reconstruye el estado, sólo condiciona el resumen nativo, y que `/handoff` es el mecanismo explícito que actualiza `docs/current-state.md`. El plugin se mantiene como experimental y eliminable si deja de ser necesario.
- **Bump de versión 0.3.0 -> 0.3.1**: documentado por ADR-012. La unidad v0.3.1 no introduce cambios en el comportamiento del generador; solo añade la capa de exploración y compactación y alinea `/handoff` con el formato canónico.
- **No modificar `opencode.jsonc`**: la verificación con `opencode debug config` confirma que el plugin se registra automáticamente desde el directorio del proyecto.
- **No usar `tsc`, `npx`, ni toolchain temporal**: el plugin se valida por carga en OpenCode y por inspección directa del código; los greps de validación sustituyen al compilador.
- **No introducir Cavemem, OpenRouter, Caveman, Ponytail Ultra ni routing adaptativo**: quedan fuera del alcance y se añaden al `docs/todos.md` como trabajo posterior.

## Archivos modificados

- `pyproject.toml` (modificado): `project.version` 0.3.0 -> 0.3.1.
- `src/python_ai_template/__init__.py` (modificado): `__version__ = "0.3.1"`.
- `uv.lock` (modificado por `uv` al detectar el bump de versión): única línea cambiada es la entrada `version = "0.3.0"` -> `version = "0.3.1"` del paquete `python-ai-template`.
- `AGENTS.md` (modificado): añadidos al mapa por tarea y al inventario de recursos el agente `scout`, la skill `context-handoff` y el plugin `structured-compaction`; reformulada la referencia a `/review` y `/handoff`; descripción del plugin corregida para reflejar que es una entrada estática sin filesystem.
- `.opencode/commands/handoff.md` (modificado): alineado con el formato canónico de la skill `context-handoff` (diez secciones obligatorias); añadido el contrato de confirmación contra `git status` y `git diff --stat`, y la prohibición de usar el resumen del plugin como autoridad.
- `.opencode/commands/review.md` (modificado): añadido el chequeo explícito de filesystem en plugins de compactación (no escriben archivos, no leen archivos vía filesystem, no usan shell, no llaman a la red, no generan logs permanentes, no modifican `output.prompt`, sólo agregan contexto auxiliar a `output.context`).
- `.opencode/skills/context-handoff/SKILL.md` (modificado): diez secciones obligatorias y relación con el plugin; descripción del plugin corregida para presentar la entrada estática sin filesystem.
- `.opencode/plugins/structured-compaction.ts` (reescrito): plugin completamente estático. Sin imports de filesystem; añade una sola cadena literal a `output.context`; no asigna `output.prompt`.
- `docs/architecture.md` (modificado): nueva sección "Capa de exploración y compactación" entre "Pipeline de validación reproducible (CI/local)" y "Dependencias". Descripción del plugin alineada con el carácter estático.
- `docs/ai/context-policy.md` (modificado): sección "Compactación y poda" ampliada con el contrato del hook `experimental.session.compacting`; nueva sección "Handoff y continuidad" alineada con la skill; sección "Lo que no se hace" ampliada con la prohibición de usar el resumen del plugin como autoridad y de inventar validaciones.
- `docs/decisions.md` (modificado): ADR-012 actualizada para reflejar el plugin estático; las once ADR anteriores conservan su contenido.
- `docs/todos.md` (modificado): añadido el completado de la unidad v0.3.1, prioridad baja nueva (varias entradas a `output.context`), prioridad media nueva (registro de desviaciones reales del plugin tras primera sesión interactiva real), trabajo posterior ampliado (Cavemem, OpenRouter, etc.).
- `docs/ai/evaluations.md` (modificado): entrada v0.3.1 reescrita (sin afirmación de lectura de archivos por parte del plugin; basada en verificación por greps, carga OpenCode y validación controlada).
- `docs/current-state.md` (reescrito a formato canónico de diez secciones por `/handoff`, con UTF-8 y tildes).

No se modificaron: `opencode.jsonc` (autodescubrimiento verificado), `tools/new_project.py`, `tools/ai/verify.py`, `tools/ai/verify_wheel.py`, `.github/workflows/ci.yml`, `tests/`, `src/python_ai_template/template/`, `README.md` (no requiere cambio: la unidad no afecta al uso ni al README público del generador), `docs/glossary.md` (los términos vigentes siguen siendo válidos), `docs/mistakes.md` (no aparecen errores recurrentes con valor futuro).

## Validaciones ejecutadas

Las validaciones se declaran en tres secciones explícitas para
distinguir entre comprobaciones estáticas (sobre archivos), pruebas
funcionales (ejecutores reales) y validaciones funcionales pendientes.

### Validaciones estáticas

Comprobaciones sobre archivos y configuración que no requieren
ejecutar el repositorio.

- **Inspección directa del código de
  `.opencode/plugins/structured-compaction.ts` (125 líneas)**:
  importa únicamente `import type { Plugin } from
  "@opencode-ai/plugin"` (línea 49, type-only); declara
  `STATIC_COMPACTION_REMINDER` como constante literal (líneas
  57-117); registra **únicamente** el hook
  `experimental.session.compacting`; el callback realiza una sola
  operación `output.context.push(STATIC_COMPACTION_REMINDER)`
  (línea 122); no asigna `output.prompt` (la única mención del
  identificador está en el docstring, línea 12, y es documentación
  de la promesa, no código).
- `grep -nE "node:fs|node:path|readFile|writeFile|readdir|stat\(" .opencode/plugins/structured-compaction.ts` -> cero
  coincidencias (cero líneas devueltas).
- `grep -c "output.context.push" .opencode/plugins/structured-compaction.ts` -> `1`.
- `grep '^## ' docs/current-state.md` -> los diez encabezados
  canónicos literales en orden:
  `Objetivo actual`, `Estado de la tarea`, `Hechos verificados`,
  `Decisiones adoptadas`, `Archivos modificados`, `Validaciones
  ejecutadas`, `Errores pendientes`, `Enfoques rechazados y motivo`,
  `Divergencias detectadas`, `Siguiente acción concreta`.
- **Revisión de `opencode.jsonc`** -> intacto (sin cambios en esta
  unidad); plugin autodescubierto por OpenCode 1.18.4 desde
  `.opencode/plugins/` con `scope: "local"`; `permission` global
  `{'edit': 'allow', 'bash': 'ask'}` se aplica a todos los
  agentes, incluido el scout (ver hallazgo m-1 del scout).
- `git diff --check` -> pass (sin marcadores de conflicto ni
  whitespace problemático).
- `git status --short` -> 11 archivos modificados + 4 untracked.
- `git diff --stat` -> `+495/-180` líneas; único cambio en
  `uv.lock` es el bump de versión aplicado por `uv` al detectar
  el cambio de `pyproject.toml`.

### Validaciones funcionales

Ejecutores reales corridos en esta sesión.

- **Carga del plugin por OpenCode 1.18.4**:
  - `opencode --version` -> `1.18.4`.
  - `opencode debug config` -> el plugin aparece en `plugin_origins`
    con `scope: "local"` desde
    `file:///home/giuseppe/projects/python-ai-template/.opencode/plugins/structured-compaction.ts`;
    agentes descubiertos `['debugger', 'documenter', 'implementer',
    'reviewer', 'scout']`; comandos descubiertos `['decision',
    'handoff', 'mistake', 'review', 'verify']`.
  - `opencode run --print-logs --log-level INFO --format json` ->
    ninguna sesión registró errores de importación ni de carga del
    plugin; el auto-descubrimiento desde `.opencode/plugins/`
    funciona sin declaración explícita en `opencode.jsonc`.
- `uv run python tools/ai/verify.py` (orquestador local): pass.
  Detalle:
  - `uv run ruff check .`: pass (0 errores).
  - `uv run ruff format --check .`: pass (`7 files already
    formatted`).
  - `uv run pyright`: pass (`0 errors, 0 warnings, 0
    informations`).
  - `uv run pytest`: pass (`33 passed`).
- `rm -rf dist && uv build` -> ok (`python_ai_template-0.3.1-py3-none-any.whl`,
  `python_ai_template-0.3.1.tar.gz`).
- `uv run python tools/ai/verify_wheel.py` (verificador del
  wheel): pass. Cuatro fuentes de la versión coinciden
  (`pyproject.toml=0.3.1`, `__version__=0.3.1`, nombre del wheel
  `0.3.1`, `METADATA Version=0.3.1`). Cinco recursos obligatorios
  presentes.
- **Sesión interactiva con el agente `scout`** sobre el empaquetado
  de `src/python_ai_template/template/` y la validación del wheel.
  Identificó correctamente `generator.py`, `template/`,
  `pyproject.toml`, `verify_wheel.py` y `ci.yml` como los archivos
  clave; explicó el flujo Hatchling -> `package data` ->
  `importlib.resources` -> `verify_wheel.py` -> job `package`;
  separó hechos, riesgos, hipótesis, preguntas abiertas y archivos
  afectados; no modificó archivos. `git status --short` permaneció
  sin cambios atribuibles al scout.
- **Ejecución interactiva de `/review`** sobre el diff de la unidad.
  Veredicto: **Aprobado con cambios menores**. Bloqueantes: ninguno.
  Mayores: ninguno. Detectó cuatro hallazgos menores:
  1. deriva histórica de `docs/todos.md` sobre v0.3.0;
  2. permisos de archivos Markdown heterogéneos en
     `.opencode/agents/`;
  3. validación estática del plugin no incorporada aún a CI;
   4. IDs de sesión demasiado específicos en `docs/current-state.md`.

- **Sesión limpia reducida de reconstrucción de contexto** en árbol
  de trabajo fresco, tras cambiar de modelo por agotamiento de cuota.
  Leyó únicamente `AGENTS.md`, `docs/current-state.md`,
  `git status --short` y `git log --oneline -3`. Reconstruyó
  correctamente: objetivo v0.3.1, 11 archivos modificados + 4
  untracked, último commit `49dfcde`, plugin estático y experimental,
  quality gates y wheel aprobados, CI remota pendiente, compactación
  real pendiente. No modificó archivos. No produjo texto corrupto.
  La variante ampliada con `docs/architecture.md` y ADR queda como
  opcional, no como bloqueo. Aprobada.

### Validaciones funcionales pendientes

No ejecutadas en esta sesión; se trasladan al siguiente bloque de
trabajo o a una sesión interactiva real.

- **Compactación real disparada por OpenCode** (umbral o prompt
  largo). Solo se verificó la carga del plugin en una sesión real
  corta y su comportamiento estático por inspección directa del
  código. La compactación real no se provocó.
- **CI remota (run GitHub Actions)**. Los cambios no están en
  `main` ni han sido empujados por el usuario.

## Errores pendientes

- (ninguno) en esta unidad tras la corrección de hallazgos de revisión.

Riesgos abiertos que requieren atención futura pero no bloquean el cierre:

- **Carácter experimental del hook**: `experimental.session.compacting` es **experimental** en OpenCode 1.18.4. Si una versión futura del SDK renombra el hook o cambia su firma, `structured-compaction.ts` dejará de registrar el callback de forma silenciosa. La mitigación es una nueva ADR y la eliminación del plugin sin tocarlo en silencio (ADR-012 lo deja por escrito).
- **Validación del plugin en sesión interactiva real**: el plugin se validó por auto-descubrimiento, carga limpia en una sesión real y greps de inspección. Una sesión interactiva larga con compactación disparada por umbral **no se ejecutó** en esta sesión. La primera sesión interactiva real deberá confirmar la salida y, si aparece una desviación, registrarla con `/mistake`.

## Enfoques rechazados y motivo

- **Reemplazar `output.prompt` en lugar de anexar a `output.context`**: rechazado por el principio de "auxiliar, no autoridad". Reemplazar el prompt por defecto hace que el plugin asuma responsabilidad sobre el resumen; anexar a `output.context` deja la responsabilidad del resumen en OpenCode.
- **Persistir el resumen de compactación en disco desde el plugin**: rechazado porque el plugin no debe escribir archivos. La persistencia corresponde a `/handoff` y `docs/current-state.md`.
- **Usar la interfaz de shell que ofrece OpenCode desde el plugin**: rechazado por las reglas operativas: el plugin no ejecuta comandos.
- **Leer `docs/current-state.md` o `pyproject.toml` desde el plugin**: rechazado por la regla explícita "no usa filesystem" del contrato de la unidad. El plugin pasa a ser estrictamente estático.
- **Anadir `tsconfig.json`, bundler o dependencias TypeScript**: rechazado por el principio de cambio mínimo en la cadena de herramientas.
- **Automatizar `/review` mediante hooks**: rechazado porque OpenCode 1.18.4 expone `command.execute.before` pero no `command.execute.after`.
- **Reutilizar `reviewer` como agente de exploración**: rechazado porque el revisor modifica archivos bajo petición explícita y no tiene contrato de solo lectura.
- **Cavemem, OpenRouter, Caveman, Ponytail Ultra y routing adaptativo**: rechazados por estar fuera del alcance y por introducir proveedores o almacenes externos.

## Divergencias detectadas

- **Ninguna** al cierre de esta sesión, tras la corrección de los hallazgos de revisión.

## Siguiente acción concreta

Cuando el usuario lo autorice, commitear el conjunto de la unidad v0.3.1 con un mensaje que cubra los cuatro archivos nuevos (`.opencode/agents/scout.md`, `.opencode/commands/review.md`, `.opencode/skills/context-handoff/SKILL.md`, `.opencode/plugins/structured-compaction.ts`) y los modificados, crear el tag `v0.3.1`, instalar localmente la nueva versión con `uv tool install .` y validar `new-python-project --version` que debe devolver `0.3.1`.

Las sesiones interactivas opcionales (scout, /review, sesión limpia reducida) se ejecutaron y se documentan en las secciones de validaciones y en `docs/ai/evaluations.md`. La variante ampliada de la sesión limpia (con `docs/architecture.md` y ADR) queda como opcional, no como bloqueo. Queda pendiente la confirmación remota en CI.

Tras la primera sesión interactiva real con el plugin `structured-compaction` que dispare una compactación por umbral, registrar cualquier desviación con `/mistake` (riesgo abierto declarado arriba, en errores pendientes).
