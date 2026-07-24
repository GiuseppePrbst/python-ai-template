# /handoff

Reescribe `docs/current-state.md` siguiendo el **formato canónico de
continuidad** definido en la skill `context-handoff`. Es breve y
operativo, y permite retomar el trabajo en otra sesión, por otra
persona o por otro agente sin la conversación previa.

## Uso

Invocar al cerrar una sesión de trabajo o cuando se quiera pasar el
relevo a otra persona o a otro agente.

## Contrato

- **Actualizar `docs/current-state.md`** con las diez secciones
  obligatorias, en este orden:
  1. **Objetivo actual**.
  2. **Estado de la tarea**.
  3. **Hechos verificados**.
  4. **Decisiones adoptadas**.
  5. **Archivos modificados**.
  6. **Validaciones ejecutadas**.
  7. **Errores pendientes**.
  8. **Enfoques rechazados y motivo**.
  9. **Divergencias detectadas**.
  10. **Siguiente acción concreta**.
- **Confirmar contra el repositorio real**:
  - Contrastar `archivos modificados` con `git status --short`.
  - Contrastar el resumen con `git diff --stat`.
  - Contrastar los hechos verificados con `git log --oneline -10`,
    con la salida de los comandos citados y con los documentos
    efectivamente leídos.
- **No crear ADR automáticamente.** Si una decisión merece una ADR,
  proponerla al usuario para que la registre con `/decision`.
- **No inventar validaciones.** Si un gate no se ejecutó, declararlo
  explícitamente en `validaciones ejecutadas` con la etiqueta
  `no ejecutado en esta sesión`.
- **No usar el resumen de compactación como autoridad.** El plugin
  `structured-compaction` produce un resumen auxiliar; el handoff
  **no** lo cita como prueba ni delega en él la verificación. Como
  mucho, lo usa como pista auxiliar cuando el `current-state.md` está
  ausente o desactualizado.
- **No introducir secretos**, claves, tokens, endpoints privados ni
  datos personales en `docs/current-state.md` ni en `docs/todos.md`.
- **No hacer commits.**

## Pasos

1. Recopilar del trabajo en curso la información de las diez
   secciones. Si alguna sección queda vacía, declarar
   explícitamente `(ninguno en esta sesión)` o `(ninguna)` según
   corresponda.
2. **Confirmar el inventario** ejecutando:
   - `git status --short`
   - `git diff --stat`
   - `git log --oneline -10`
3. **Ejecutar los gates que correspondan** al cierre y recoger su
   resultado. Si un gate no se ejecuta (por ejemplo, el wheel porque
   el cambio no toca empaquetado), declararlo en `validaciones
   ejecutadas` con `no ejecutado en esta sesión`.
4. **Reescribir `docs/current-state.md`** con las diez secciones en
   orden. Evitar prosa extensa: listas y frases cortas.
5. Si aparecen tareas nuevas no triviales, añadirlas a `docs/todos.md`
   con su prioridad.
6. Si se cerró una decisión arquitectónica que no estaba registrada,
   proponerla al usuario para registrarla con `/decision`.
7. Si la sesión dejó un error recurrente documentable, proponer al
   usuario registrarlo con `/mistake`.
8. Si `docs/current-state.md` está alineado con `git status` y los
   gates, declarar la sesión lista para el relevo.

## Salida esperada

- `docs/current-state.md` reescrito con las diez secciones
  obligatorias, en orden.
- Cambios en `docs/todos.md` si corresponde.
- Propuestas (no acciones) de entradas en `docs/decisions.md` o
  `docs/mistakes.md` si corresponde.
- Confirmación explícita de qué validaciones se ejecutaron y cuáles
  no.
