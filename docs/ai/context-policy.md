# Política de contexto

Cómo se gestiona el contexto entre sesiones, agentes y tareas. Esta política aplica junto con `AGENTS.md`, con `docs/architecture.md`, con las ADR vigentes y con la configuración de OpenCode (`opencode.jsonc` del proyecto, `~/.config/opencode/opencode.json` global).

## Principios

- **Contexto mínimo siempre presente.** En cada sesión se carga solo lo necesario para la tarea: `AGENTS.md` y los documentos directamente relacionados con lo que se va a hacer.
- **Recuperación selectiva.** El resto se obtiene bajo demanda con herramientas de búsqueda, lectura de archivos específicos o skills (`python-quality`, `architecture-review`, `context-handoff`).
- **No cargar toda la documentación en cada tarea.** Cargar `docs/` completo por sesión desperdicia contexto y reduce la capacidad de razonamiento efectiva.
- **`docs/current-state.md` es el punto de continuidad.** Al inicio de cada sesión se lee este archivo para retomar el trabajo sin re-explorar el repositorio. Se reescribe al cierre con `/handoff` siguiendo el formato canónico de la skill `context-handoff` (diez secciones obligatorias).
- **El código es la evidencia final.** Cuando `docs/` y el código divergen, prevalece el código. La divergencia se corrige actualizando `docs/`, nunca "arreglando" el código para que coincida con un documento obsoleto.
- **El plugin `structured-compaction` es un resumen auxiliar, no autoridad documental.** Cuando OpenCode compacta la conversación, el plugin `.opencode/plugins/structured-compaction.ts` añade una sola entrada compacta a `output.context` para recordar al compactor qué preservar. Esa entrada **no sustituye** a `docs/current-state.md` ni a `/handoff`. Ver ADR-012.

## Margen reservado

La configuración de OpenCode reserva `reserved: 16000` tokens para evitar quedarse sin contexto en operaciones largas. Esta reserva es deliberada: preferible detener y compactar a perder calidad de respuesta. El valor se define en `opencode.jsonc` y se refleja en la configuración global.

## Compactación y poda

- `compaction.auto: true`: OpenCode compacta la conversación cuando el contexto se acerca al límite.
- `compaction.prune: true`: poda mensajes y resultados antiguos que ya no son necesarios.
- Estas opciones viven en `opencode.jsonc` (proyecto) y se reflejan en `~/.config/opencode/opencode.json` (global).
- En OpenCode 1.18.4 el hook `experimental.session.compacting` se invoca **antes** de que el LLM genere el resumen de compactación. El plugin `structured-compaction` lo registra y, en cada invocación, añade **una sola entrada estática** (cadena literal definida en el propio plugin) a `output.context`. Esa entrada **no lee** `docs/current-state.md` ni `pyproject.toml`: contiene instrucciones recordatorias para el mecanismo nativo de compactación, en particular las diez secciones canónicas del handoff (`objetivo actual`, `estado de la tarea`, `hechos verificados`, `decisiones adoptadas`, `archivos modificados`, `validaciones ejecutadas`, `errores pendientes`, `enfoques rechazados y motivo`, `divergencias detectadas`, `siguiente acción concreta`) y los límites del resumen. El plugin es estrictamente estático: no usa filesystem, no usa shell, no usa red, no genera logs permanentes, no persiste información, no reconstruye el estado. La reconstrucción del estado la hacen el propio mecanismo nativo de compactación de OpenCode y el comando `/handoff`. El hook es **experimental**; cualquier cambio de comportamiento se documenta con una nueva ADR.

## Handoff y continuidad

- El formato canónico de `docs/current-state.md` vive en la skill `context-handoff`. Tiene **diez secciones obligatorias**, en este orden: objetivo actual, estado de la tarea, hechos verificados, decisiones adoptadas, archivos modificados, validaciones ejecutadas, errores pendientes, enfoques rechazados y motivo, divergencias detectadas, siguiente acción concreta.
- El comando `/handoff` reescribe `docs/current-state.md`. **No** acumula ediciones sobre el archivo previo.
- `/handoff` confirma contra `git status --short` y `git diff --stat`, **no** contra el resumen del plugin.
- El agente `scout` se usa, cuando hay duda sobre el estado del árbol de trabajo, para verificar el repositorio antes de aceptar un handoff como vigente. El scout **no modifica** el handoff; si encuentra divergencias, las devuelve al usuario o a `implementer`.

## Lo que no se hace

- No se copia documentación entera en el prompt.
- No se mantiene contexto residual entre tareas no relacionadas.
- No se confía en la memoria del modelo entre sesiones: `docs/current-state.md` es el mecanismo de continuidad.
- No se reduce el margen reservado para encajar más conversación a costa de calidad.
- No se usa el resumen del plugin `structured-compaction` como autoridad documental. Se trata como pista auxiliar.
- No se inventa el resultado de validaciones en `docs/current-state.md`. Si un gate no se ejecutó, se declara explícitamente.

## Documentos relacionados

- `AGENTS.md`: mapa de documentos por tarea y quality gates.
- `docs/current-state.md`: estado al cierre y al inicio de cada sesión.
- `docs/architecture.md`: capa de exploración y compactación (scout, /review, context-handoff, plugin).
- `docs/decisions.md`: ADR vigentes, en particular ADR-012 sobre el plugin de compactación.
- `docs/glossary.md`: terminología, incluidos los términos `compactación` y `reserva de contexto`.
- `.opencode/skills/context-handoff/SKILL.md`: formato canónico del handoff.
- `.opencode/plugins/structured-compaction.ts`: plugin de compactación estructurada.
- `opencode.jsonc`: parámetros de compactación y permisos.
