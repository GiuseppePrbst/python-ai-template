# /handoff

Actualiza `docs/current-state.md` para dejar el trabajo listo para retomar en otra sesión o por otra persona. Es breve y operativo.

## Uso

Invocar al cerrar una sesión de trabajo o cuando se quiera pasar el relevo a otra persona o a otro agente.

## Pasos

1. Recopilar del trabajo en curso:
   - **Objetivo** de la sesión.
   - **Estado final**: qué se hizo y qué quedó pendiente.
   - **Archivos modificados o creados** durante la sesión.
   - **Validaciones ejecutadas** y su resultado (calidad, formato, tipos, tests).
   - **Decisiones tomadas** o que requieren aprobación (`/decision`).
   - **Problemas pendientes**, bloqueos o riesgos abiertos.
   - **Próxima acción** concreta, una sola si es posible.
2. Reescribir `docs/current-state.md` con esa información, en ese orden, de forma breve.
3. Si hay tareas nuevas no triviales, añadirlas a `docs/todos.md` con su prioridad.
4. Si se cerró una decisión que no estaba registrada, hacerlo con `/decision`.
5. Si la sesión dejó un error recurrente documentable, hacerlo con `/mistake`.

## Reglas

- `docs/current-state.md` debe permitir retomar el trabajo sin la conversación previa.
- Evitar prosa extensa: listas y frases cortas.
- No introducir secretos, claves, endpoints ni datos personales en `docs/current-state.md` ni en `docs/todos.md`.
- No hacer commits.
- Si la sesión no produjo cambios, indicarlo explícitamente en lugar de dejar el archivo obsoleto.

## Salida esperada

- `docs/current-state.md` reescrito con las secciones: objetivo, estado, archivos modificados, validaciones, decisiones, problemas pendientes, próxima acción.
- Cambios en `docs/todos.md` si corresponde.
- Cambios en `docs/decisions.md` o `docs/mistakes.md` si corresponde.
