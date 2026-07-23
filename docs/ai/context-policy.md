# Política de contexto

Cómo se gestiona el contexto entre sesiones, agentes y tareas. Esta política aplica junto con `AGENTS.md` y con la configuración de OpenCode (`opencode.jsonc` del proyecto, `~/.config/opencode/opencode.json` global).

## Principios

- **Contexto mínimo siempre presente.** En cada sesión se carga solo lo necesario para la tarea: `AGENTS.md` y los documentos directamente relacionados con lo que se va a hacer.
- **Recuperación selectiva.** El resto se obtiene bajo demanda con herramientas de búsqueda, lectura de archivos específicos o skills (`python-quality`, `architecture-review`).
- **No cargar toda la documentación en cada tarea.** Cargar `docs/` completo por sesión desperdicia contexto y reduce la capacidad de razonamiento efectiva.
- **`docs/current-state.md` es el punto de continuidad.** Al inicio de cada sesión se lee este archivo para retomar el trabajo sin re-explorar el repositorio. Se reescribe al cierre con `/handoff`.
- **El código es la evidencia final.** Cuando `docs/` y el código divergen, prevalece el código. La divergencia se corrige actualizando `docs/`, nunca "arreglando" el código para que coincida con un documento obsoleto.

## Margen reservado

La configuración de OpenCode reserva `reserved: 16000` tokens para evitar quedarse sin contexto en operaciones largas. Esta reserva es deliberada: preferible detener y compactar a perder calidad de respuesta. El valor se define en `opencode.jsonc` y se refleja en la configuración global.

## Compactación y poda

- `compaction.auto: true`: OpenCode compacta la conversación cuando el contexto se acerca al límite.
- `compaction.prune: true`: poda mensajes y resultados antiguos que ya no son necesarios.
- Estas opciones viven en `opencode.jsonc` (proyecto) y se reflejan en `~/.config/opencode/opencode.json` (global).

## Lo que no se hace

- No se copia documentación entera en el prompt.
- No se mantiene contexto residual entre tareas no relacionadas.
- No se confía en la memoria del modelo entre sesiones: `docs/current-state.md` es el mecanismo de continuidad.
- No se reduce el margen reservado para encajar más conversación a costa de calidad.

## Documentos relacionados

- `AGENTS.md`: mapa de documentos por tarea y quality gates.
- `docs/current-state.md`: estado al cierre y al inicio de cada sesión.
- `docs/architecture.md` y `docs/decisions.md`: contexto estable del proyecto que se puede citar sin recargar.
- `opencode.jsonc`: parámetros de compactación y permisos.
