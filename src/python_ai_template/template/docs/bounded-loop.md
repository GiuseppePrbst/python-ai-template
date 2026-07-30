# Contrato bounded execution loop

Contrato canónico y reutilizable para evitar que cualquier agente, subagente o
worker de este repositorio (y de los proyectos generados por esta plantilla)
produzca un *runaway loop* / *no-progress loop*. Es la fuente de verdad
operativa del control anti-loop.

## Arquitectura del control anti-loop

El control anti-loop se organiza en cuatro capas:

1. **Contrato consultivo de agentes** (este documento). Declara las reglas que
   los agentes autónomos deben respetar. Los agentes
   (`.opencode/agents/implementer.md`, `.opencode/agents/debugger.md`) lo
   referencian explícitamente.

2. **Especificación ejecutable local**. El módulo
   `tools/ai/bounded_loop_contract.py` es un simulador de contrato que
   implementa las reglas de transición, los estados terminales y los límites
   en Python puro. No controla tool calls reales ni cancela generación del
   modelo. Los tests en `tests/test_bounded_loop.py` importan esta
   especificación y verifican los 22 escenarios exigidos.

3. **Verificación estática**. `tools/ai/verify_opencode.py` comprueba que el
   documento existe, que contiene los marcadores obligatorios, y que los
   agentes autónomos y el comando `/handoff` referencian el contrato.

4. **Watchdog runtime externo** (no implementado en esta unidad). El control
   real de tool calls, la cancelación efectiva del modelo y el enforcement
   del presupuesto requieren soporte del orquestador/runtime. Esta unidad
   aporta los contratos y la validación; el runtime aporta la parada. Ver
   "Frontera explícita" más abajo.

Los agentes autónomos referencian el contrato; el verificador estático exige
esa referencia y la presencia de los marcadores aquí declarados.

## Definición de ciclo productivo

Una iteración sólo es **productiva** si produce al menos uno de los
siguientes resultados verificables:

- nueva evidencia (logs, diffs, contenido nuevo en el working tree);
- cambio verificable del working tree (`git diff`, `git status`);
- nuevo resultado de test (un test que antes no se ejecutaba o un test
  cuyo veredicto cambió);
- reducción demostrable del conjunto de fallos;
- transición explícita del estado de la tarea (p. ej. fase
  completada, hipótesis descartada, blocker registrado);
- escalamiento explícito (estado `ESCALATED`, propuesta de dividir la
  tarea, derivación a otro agente).

Repetir el mismo comando, diagnóstico o intención de prueba sin uno de
esos resultados es **no-progress**. Toda iteración no-progress consume
presupuesto de no-progress.

## Protocolo de bounded execution loop

Un worker conforme a este contrato mantiene, como mínimo, los siguientes
campos durante la ejecución de una tarea. El estado crítico debe poder
persistirse entre invocaciones (ver "Persistencia" abajo).

| Campo                  | Tipo           | Significado                                                                                         |
|------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| `task_id`              | str            | Identificador estable de la tarea; sobrevive a handoffs.                                            |
| `phase_id`             | str            | Identificador de la fase actual dentro de la tarea.                                                 |
| `step_number`          | int            | Contador de pasos consumidos en la fase actual.                                                     |
| `step_budget`          | int            | Presupuesto explícito de pasos por fase; al agotarse termina la fase.                               |
| `deadline`             | ISO 8601 UTC   | Fecha/hora límite global de la tarea; al rebasarse termina la tarea.                                |
| `action_fingerprint`   | str            | Huella estable de la acción: herramienta + comando normalizado + cwd + inputs relevantes + HEAD.     |
| `state_before`         | str            | Resumen del estado del working tree y de los resultados previos, capturado antes de la acción.      |
| `expected_state_change`| str            | Lo que el worker espera que cambie tras ejecutar la acción.                                         |
| `state_after`          | str            | Lo que cambió realmente tras la acción; vacío si no hubo cambio.                                    |
| `progress_detected`    | bool           | `True` si `state_after` introduce al menos uno de los resultados de "ciclo productivo".            |
| `same_action_count`    | int            | Conteo de ejecuciones consecutivas con el mismo `action_fingerprint` (éxito o no).                   |
| `retry_count`          | int            | Reintentos del mismo `action_fingerprint` (sólo cuentan si la acción previa falló).                 |
| `no_progress_count`    | int            | Iteraciones consecutivas con `progress_detected == False`.                                          |
| `terminal_status`      | enum           | Uno de los seis estados terminales (ver abajo).                                                     |
| `escalation_reason`    | str \| None    | Razón del escalamiento si `terminal_status` es `ESCALATED` o `BLOCKED_LOOP`.                        |

## Fingerprint de acción

El `action_fingerprint` se calcula conceptualmente desde:

- herramienta invocada (nombre estable, sin auto-inyecciones del LLM);
- comando o acción exacta, con argumentos normalizados
  (orden canónico, sin flags redundantes, paths absolutos resueltos);
- working directory;
- inputs relevantes (contenido del archivo sobre el que se actúa,
  flags efectivos, variables de entorno explícitas);
- HEAD o estado base cuando la acción lo modifique.

Dos acciones con el mismo fingerprint no pueden ejecutarse
indefinidamente. Una acción ejecutada con éxito **no** debe repetirse
en la misma fase: está prohibido volver a invocar un comando cuyo
resultado anterior ya cubría la evidencia que la fase necesitaba.

## Límites mínimos

Estos límites son el suelo del contrato. Una implementación puede
imponerlos más estrictos, pero nunca más laxos.

- **Máximo 1 retry** del mismo `action_fingerprint`. El segundo
  intento del mismo fingerprint, tras uno fallido, debe terminar la
  fase con `BLOCKED_LOOP` o `ESCALATED`.
- **Máximo 2 iteraciones consecutivas sin progreso**
  (`no_progress_count <= 2`). Al alcanzar el límite, la fase termina
  con `BLOCKED_LOOP` o `ESCALATED`.
- **Presupuesto explícito de pasos por fase** (`step_budget`). El
  agotamiento termina la fase con `BLOCKED` o `ESCALATED`; nunca se
  aumenta el presupuesto silenciosamente.
- **Timeout por comando**. Cada comando declara un timeout; superado,
  el comando se considera fallido y se contabiliza en `retry_count`.
- **Deadline global de tarea**. Alcanzada la `deadline`, el worker
  emite `BLOCKED` o `CANCELLED` y se detiene sin otra acción.
- **Prohibido repetir un comando exitoso**.
- **Prohibido repetir el mismo diagnóstico textual** cuando el
  fingerprint semántico (no sólo textual) coincide con un
  `state_after` anterior sin evidencia nueva.
- **Un solo primer fallo corregido por iteración**. Si en una sola
  iteración se acumulan dos o más correcciones distintas, la fase
  termina con `BLOCKED_LOOP` antes de aplicar la segunda.
- **Después del límite, terminar sin otra acción**. No se permite un
  último intento "por si acaso".

## Estados terminales

Lista cerrada, exhaustiva y mutuamente excluyente. Toda ejecución
conforme termina en exactamente uno de estos estados. No hay estado
intermedio visible para el orquestador.

| Estado        | Significado                                                                                                  |
|---------------|--------------------------------------------------------------------------------------------------------------|
| `COMPLETED`   | La fase terminó con el `expected_state_change` cumplido y evidencia verificable.                             |
| `FAILED`      | La fase terminó por un fallo no relacionado con el loop (defecto confirmado, causa raíz documentada).        |
| `BLOCKED`     | La fase terminó por una dependencia externa (input ausente, decisión humana pendiente).                      |
| `BLOCKED_LOOP`| La fase terminó porque se alcanzó un límite del contrato. Ver reglas de activación abajo.                    |
| `ESCALATED`   | La fase terminó porque el worker juzgó que requiere un humano o un agente con permisos distintos.             |
| `CANCELLED`   | La fase terminó por orden explícita del usuario o por `deadline` global alcanzada.                           |

`BLOCKED_LOOP` se activa cuando se cumple **al menos uno**:

- el mismo `action_fingerprint` supera el límite de reintentos;
- `no_progress_count` alcanza el límite;
- se repite una salida (`state_after`) sin nueva evidencia;
- el agente intenta reiniciar una fase ya marcada como completada;
- el agente ignora dos veces una condición de parada explícita.

## Regla de transición

Antes de cada acción, el worker debe declarar:

- qué evidencia espera obtener (`expected_state_change`);
- qué estado debería cambiar;
- cómo sabrá que la acción terminó (criterio de éxito observable).

Después de la acción debe registrar:

- evidencia obtenida (resumen, no logs completos);
- cambio real (`state_after`);
- siguiente estado.

Sin cambio real verificable, la iteración consume el presupuesto de
`no_progress_count`. El worker no puede ocultar el `state_after`
vacío: cualquier intento de "rellenar" el campo con texto repetitivo
consume el mismo presupuesto.

## Persistencia

El estado crítico no puede depender sólo del chat. El worker mantiene
un checkpoint local, versionable o efímero según corresponda, que
permite recuperar al menos:

- última fase completada;
- último comando ejecutado;
- último resultado;
- fingerprints ejecutados;
- retries usados;
- archivos modificados;
- gates pendientes;
- condición de parada.

Formato preferido: JSON o JSONL local con schema cerrado. **No** se
introduce SQLite ni servicios externos en esta unidad. **No** se
introducen dependencias de runtime.

El checkpoint se almacena en una ruta local estable
(`.opencode/state/<task_id>.json` o equivalente declarado por el
runtime). Si la ruta exacta no puede garantizarse desde la plantilla,
el contrato declara la **forma** del schema; el runtime decide la
**ubicación**.

## Frontera explícita

La especificación ejecutable (`tools/ai/bounded_loop_contract.py`) y los tests
(`tests/test_bounded_loop.py`) **no implementan**:

- watchdog runtime;
- contador real de tool calls de OpenCode;
- cancelación efectiva del modelo;
- persistencia operacional de checkpoints;
- enforcement externo del presupuesto.

Lo que esta unidad **sí** garantiza:

- declarar este contrato en `docs/bounded-loop.md` y exigir su
  referencia en los agentes autónomos y en el comando `/handoff`;
- una especificación ejecutable reutilizable en
  `tools/ai/bounded_loop_contract.py` que modela las reglas de
  transición, los estados terminales, los límites y `ResourceLimit`;
- validar estáticamente la presencia del contrato, de los marcadores
  obligatorios, y de la referencia en los agentes mediante
  `tools/ai/verify_opencode.py`;
- exigir handoffs estructurados (invocación de `/handoff`) cuando un
  worker termina en estado distinto de `COMPLETED`;
- documentar y evaluar a posteriori si los agentes cumplen el
  contrato (ver `docs/ai/evaluations.md`).

Lo que requiere soporte del orquestador/runtime:

- impedir físicamente que el modelo genere texto repetido;
- cancelar tool calls ya en curso si el orquestador no expone un
  mecanismo soportado para ello;
- detectar en tiempo real que el LLM está decidiendo iterar sin
  progreso (sólo puede detectarlo a posteriori);
- imponer el `deadline` si el runtime no interrumpe la generación;
- mantener un watchdog persistente entre invocaciones;
- contabilizar tool calls reales de OpenCode.

El control completo de un *runaway loop* requiere un **watchdog
externo en el orquestador/runtime**. Esta unidad aporta los
contratos, la especificación ejecutable, los fingerprints y la
validación; el runtime aporta la parada. Esta frontera se documenta
también en `docs/architecture.md`.

## Especificación ejecutable

El módulo `tools/ai/bounded_loop_contract.py` contiene:

- **Constantes**: `TERMINAL_*`, `DEFAULT_*`.
- **Tipos**: `StepOutcome`, `Action`, `LoopState`, `ResourceLimit`.
- **Funciones**: `run_step`, `handle_resource_limit`.
- **Utilería**: `_advance`, `_set_terminal`, `_sanitize`.

Los tests en `tests/test_bounded_loop.py` importan desde este módulo y
verifican los 22 escenarios. Cualquier cambio en las reglas del loop debe
mantener estos tests.

## Verificación estática

`tools/ai/verify_opencode.py` comprueba (vía `verify_bounded_loop_contract`):

1. Que `docs/bounded-loop.md` (y su copia en el template) existe.
2. Que contiene los marcadores obligatorios (`bounded execution loop`,
   `action_fingerprint`, `step_budget`, `retry_count`, `no_progress_count`,
   `terminal_status`, `BLOCKED_LOOP`, `COMPLETED`, `resource_limit`,
   `/handoff`, `checkpoint`, `watchdog externo`).
3. Que los agentes autónomos (`implementer.md`, `debugger.md`) y el comando
   `/handoff` contienen la referencia canónica `docs/bounded-loop.md`.
4. Que la copia raíz y la del template están sincronizadas byte a byte.

## Salida del worker

La salida visible de un worker conforme a este contrato **no contiene
bloques `<think>` ni deliberación privada**: el razonamiento se
declara explícitamente en el `state_before`, en el
`expected_state_change` y en el `state_after`. El resto es
ejecución observable. Esta regla es una restricción contractual, no
técnica: depende de la disciplina del agente y de la política del
modelo. La plantilla la documenta; el runtime la aplica cuando puede.

## Handoff al detenerse

Todo worker conforme invoca el comando `/handoff` cuando su
`terminal_status` es distinto de `COMPLETED`. En particular, en los
estados `BLOCKED_LOOP` y `ESCALATED`, el handoff incluye:

- `terminal_status` efectivo;
- `escalation_reason` (qué límite se activó o por qué se escaló);
- últimos `action_fingerprint` ejecutados y sus `state_after`;
- valores finales de `step_number`, `step_budget`, `retry_count` y
  `no_progress_count`.

El comando `/handoff` (`.opencode/commands/handoff.md`) reconoce
explícitamente esta obligación como parte de su contrato.