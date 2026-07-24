# context-handoff

Skill para preparar, revisar y consumir un handoff de sesión. Carga
esta skill al inicio de una sesión, al cierre de un bloque de trabajo
y cuando se use `/handoff` o cuando se necesite reconstruir contexto
a partir de `docs/current-state.md`.

## Cuándo cargar

- Inicio de una sesión, antes de empezar a editar o ejecutar
  comandos.
- Cierre de un bloque de trabajo, antes de invocar `/handoff`.
- Reconstrucción de contexto en una sesión nueva o por una persona
  distinta.
- Lectura crítica de un `docs/current-state.md` heredado de otra
  sesión.
- Coordinación con el agente `scout` cuando se necesite verificar
  el estado real del repositorio antes de aceptar un handoff.

## Contrato obligatorio de handoff

`docs/current-state.md` es la fuente de verdad para retomar el
trabajo entre sesiones, agentes y personas. Su contenido debe
respetar, en este orden, las **diez secciones obligatorias**:

1. **Objetivo actual** — qué se está haciendo en una sola frase.
2. **Estado de la tarea** — qué se hizo y qué quedó pendiente.
3. **Hechos verificados** — comprobaciones realizadas contra
   `git status`, `git diff --stat`, commits recientes, comandos
   concretos. Cada hecho con su fuente.
4. **Decisiones adoptadas** — ADR nuevas, decisiones explícitas o
   referencias cruzadas a ADR vigentes. Incluir también las
   decisiones implícitas que requieren `/decision`.
5. **Archivos modificados** — rutas relativas a la raíz del
   repositorio, sin absolutas, con la naturaleza del cambio
   (creado, modificado, borrado).
6. **Validaciones ejecutadas** — quality gates corridos y su
   resultado. Indicar siempre `ruff check`, `ruff format --check`,
   `pyright` y `pytest` cuando aplique, más la verificación del
   wheel si el cambio toca el empaquetado. Indicar **explícitamente**
   qué validaciones no se ejecutaron.
7. **Errores pendientes** — bugs, fallos de validación, regresiones
   o riesgos abiertos. Distinguir errores bloqueantes de
   observaciones.
8. **Enfoques rechazados y motivo** — alternativas que se
   consideraron y se descartaron, con la razón del descarte.
   Esta sección es **obligatoria** aunque quede en `(ninguno)`.
9. **Divergencias detectadas** — incoherencias entre `docs/` y el
   código, entre el handoff y `git status`, o entre lo que el
   plugin de compactación resume y el repositorio real. **Se
   registran sin resolverse** desde el handoff; la resolución
   corresponde a `implementer` o `documenter`.
10. **Siguiente acción concreta** — una sola acción, bien definida,
    que pueda ejecutar el siguiente agente o persona sin reexplorar
    el repositorio.

## Reglas

- **Markdown es la fuente de verdad.** El formato canónico se aplica
  en `docs/current-state.md`. El comando `/handoff` reescribe este
  archivo, no lo acumula.
- **Confirmar contra el repositorio real.** Antes de cerrar un
  handoff, contrastar `archivos modificados` con `git status`, el
  `resumen del cambio` con `git diff --stat` y los `hechos
  verificados` con los comandos o lecturas que los sostienen.
- **No crear ADR automáticamente.** Si una decisión arquitectónica
  merece una ADR, se propone al usuario para que la registre con
  `/decision`.
- **No inventar validaciones.** Si un gate no se ejecutó, se declara
  explícitamente; no se afirma como aprobado.
- **No usar el resumen de compactación como autoridad.** El plugin
  `structured-compaction` produce un resumen auxiliar; el handoff
  no lo cita como prueba y no delega en él la verificación.
- **Listas y frases cortas.** Evitar prosa larga; cada sección debe
  poder leerse en segundos.
- **Cero secretos.** Nunca incluir claves, tokens, endpoints
  privados ni datos personales. Si aparecen al pasar, omitirlos y
  mencionarlo en `errores pendientes`.
- **Cero logs completos.** Si un log es relevante, referenciarlo por
  ruta y rango, no copiarlo entero.
- **Cero rutas absolutas.** Usar siempre rutas relativas a la raíz
  del repositorio.
- **Coherencia con el código.** Si `docs/current-state.md` y el
  código divergen, prevalece el código y se corrige el documento.

## Relación con el plugin `structured-compaction`

El plugin `structured-compaction` (ver ADR-012) complementa al
`/handoff`: cuando OpenCode dispara una compactación automática
durante una sesión larga, el plugin añade a `output.context` una
**entrada estática** (cadena literal definida en el propio plugin)
que **no lee** `docs/current-state.md`, **no lee** `pyproject.toml`
y **no** reconstruye el estado real del repositorio. Esa entrada es
una **instrucción recordatoria** para el mecanismo nativo de
compactación: enumera las diez secciones canónicas del handoff
(objetivo, estado de la tarea, hechos verificados, decisiones
adoptadas, archivos modificados, validaciones ejecutadas, errores
pendientes, enfoques rechazados y motivo, divergencias
detectadas, siguiente acción concreta), distingue hechos,
decisiones, hipótesis y pendientes, y marca los límites del
resumen (sin secretos, sin logs completos, sin resultados
inventados). Ese recordatorio **no sustituye** a `/handoff`:

- `/handoff` se invoca al **cierre explícito** de un bloque de
  trabajo por una persona o un agente.
- La compactación estructurada actúa **durante** una sesión larga,
  sin intervención del usuario.

El plugin **no** escribe en `docs/current-state.md` y **no** lee
ningún archivo del repositorio. La fuente de verdad al cierre
sigue siendo `/handoff` y el archivo que reescribe. El handoff
**no** usa el resumen del plugin como autoridad: lo trata solo
como una pista auxiliar.

## Relación con el agente `scout`

`scout` es el agente de solo lectura que verifica el estado real del
repositorio. Cuando se recibe un handoff y se sospecha que el árbol
de trabajo ha cambiado, se invoca a `scout` antes de aceptar el
handoff como vigente. El scout devuelve hechos, inferencias e
hipótesis con cita, pero **no modifica** el handoff: si hay
divergencias, se registran en `divergencias detectadas`.

## Lista de comprobación al inicio de una sesión

1. Leer `docs/current-state.md` completo.
2. Si hay secciones vacías o ausentes, pedir aclaración antes de
   continuar.
3. Contrastar el objetivo con `git status --short` y, si procede,
   `git log --oneline -10`.
4. Si la sesión cambió de agente, derivar a `scout` para confirmar
   el inventario de archivos modificados.
5. Ejecutar `/verify` antes de iniciar cambios no triviales.

## Lista de comprobación al cierre de una sesión

1. Confirmar que las diez secciones obligatorias del formato
   canónico están presentes y en orden.
2. Confirmar que `archivos modificados` coincide con
   `git status --short` y que los archivos listados existen.
3. Confirmar que `validaciones ejecutadas` refleja el último
   `uv run python tools/ai/verify.py` y, si aplica, el último
   `verify_wheel.py`. Indicar **explícitamente** qué gates no
   se corrieron.
4. Confirmar que `errores pendientes` lista los bloqueantes reales
   y no meras observaciones.
5. Confirmar que `enfoques rechazados y motivo` está explícita,
   aunque diga `(ninguno en esta sesión)`.
6. Confirmar que `divergencias detectadas` lista las
   incoherencias entre `docs/` y el código, o declara
   `(ninguna)`.
7. Confirmar que `siguiente acción concreta` es una sola acción
   ejecutable.

## Documentos relacionados

- `AGENTS.md`: mapa de documentos por tarea y quality gates.
- `.opencode/commands/handoff.md`: contrato operativo del comando.
- `.opencode/agents/scout.md`: verificación de solo lectura.
- `.opencode/commands/review.md`: revisión manual del diff.
- `.opencode/plugins/structured-compaction.ts`: plugin de
  compactación estructurada (ver ADR-012).
- `docs/architecture.md`: límites y componentes del proyecto.
- `docs/decisions.md`: ADR vigentes, en particular ADR-012.
- `docs/ai/context-policy.md`: política de gestión de contexto.
