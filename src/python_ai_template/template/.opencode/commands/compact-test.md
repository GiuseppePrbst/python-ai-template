# /compact-test

Prueba manual reproducible y desechable del plugin
`structured-compaction`. Diseñada para validar que, ante una
compactación nativa de OpenCode 1.18.4, el resumen post-compactación
preserva (o pierde, según el caso) el contenido del checkpoint
distribuido en `.opencode/fixtures/`.

Este comando **no** modifica ADR ni `docs/current-state.md`
automáticamente. Si la prueba revela un hallazgo, se registra en
`docs/mistakes.md` o se propone una nueva ADR según corresponda.

## Fixtures distribuidos

- **Checkpoint**: `.opencode/fixtures/compaction-checkpoint.md`.
  Fixture estático, completamente sintético, sin referencias al
  proyecto real. Contiene los 10 headings canónicos y los 11
  marcadores exactos `OBJECTIVE-01`, `STATE-01`, `FACT-01`,
  `FACT-02`, `DECISION-01`, `FILE-01`, `VALIDATION-01`,
  `ERROR-01`, `REJECTED-01`, `DIVERGENCE-01`, `NEXT-01`.
- **Filler**: `.opencode/fixtures/compaction-filler.md`. Texto
  neutro y metalingüístico, sin hechos, decisiones, marcadores,
  cifras, fechas, nombres ni rutas. Sirve para empujar el contexto
  hacia el umbral de compactación. **Mismo filler para todos los
  modelos**.

Ambos archivos viven en `.opencode/fixtures/` (raíz operativa) y
en `src/python_ai_template/template/.opencode/fixtures/`
(template canónico). Son byte a byte idénticos; la copia canónica
es la del template.

## Cuando usarlo

- Tras cualquier cambio al plugin
  `src/python_ai_template/template/.opencode/plugins/structured-compaction.ts`.
- Tras cualquier cambio al formato canónico de
  `docs/current-state.md`.
- Antes de rotar la versión mayor del SDK OpenCode.
- Después de cualquier actualización de OpenCode que pueda afectar al
  hook `experimental.session.compacting`.
- Antes de tomar la decisión final de mantener, simplificar,
  eliminar o continuar experimental el plugin.

## Procedimiento

El procedimiento es idéntico por modelo. Cada modelo recibe su
propia clasificación.

1. **Precondiciones operativas.**
   - `opencode --version` devuelve la versión declarada en
     `.opencode/package.json` (vigente: `1.18.4`). Si es otra, se
     documenta y se decide caso por caso.
   - `opencode debug config` lista `structured-compaction` con
     `scope: "local"`.
   - `git status --short` vacío.
   - Working tree en `main`, al día con `origin/main`.

2. **Iniciar sesión limpia** de OpenCode. Si la interfaz expone
   mecanismo soportado y verificable para "sesión nueva", usarlo.
   Si no, abrir sesión fresca.

3. **Cargar el checkpoint** en la conversación inicial. Pegar
   literalmente el contenido de
   `.opencode/fixtures/compaction-checkpoint.md`. No reformular.

4. **Cargar el filler** en la misma sesión. Pegar literalmente el
   contenido de `.opencode/fixtures/compaction-filler.md`.

5. **Cargar contexto** mediante diálogo natural relacionado con el
   checkpoint. **Máximo 3 ciclos** de carga (preguntas y respuestas
   que soliciten reformulaciones, desgloses o ampliaciones, sin
   introducir contenido nuevo).

6. **Disparar la compactación.**
   - Si OpenCode expone un comando o API soportada y verificable
     para forzar compactación, documentar y usar.
   - Si no, continuar el diálogo hasta que el umbral automático se
     alcance.
   - **Nunca** inventar un comando no documentado.

7. **Capturar el evento** de compactación desde los logs de la
   **misma sesión** (no de una ejecución separada). Si OpenCode
   expone un identificador de sesión (`ses_xxx`), capturar el ID.

8. **Capturar el resumen post-compactación** en la misma sesión,
   inmediatamente después del evento.

9. **Ejecutar `git status --short`** desde la raíz. Debe estar
   **vacío**.

10. **Clasificar** según la rúbrica de la sección "Rúbrica".

11. **Registrar** con `tools/ai/record_evaluation.py --write`.
    **`--duration-minutes` se incluye solo si la duración fue
    realmente medida**; en caso contrario, se omite.

12. **Detener** la prueba al confirmar compactación o al agotar el
    presupuesto.

### Presupuesto por corrida

| Concepto | Límite |
|----------|--------|
| Ciclos de carga | 3 |
| Duración total máxima | 20 minutos |
| Condición de parada | Compactación confirmada o presupuesto agotado |

Excedido el presupuesto sin compactación confirmada: la corrida se
clasifica `inconclusive`.

### Restricciones durante la prueba

- Checkpoint y filler **literales**, no reformulados.
- Sin secretos reales en ningún momento.
- Sin telemetría externa, sin envío de logs remotos, sin routing
  automático.
- Sin Cavemem, OpenRouter, Caveman, Ponytail Ultra.
- Sin medición de tokens (ADR-013 lo prohíbe).
- Sin inventar comandos para forzar compactación.
- Sin logs commiteados: el log se almacena en
  `/tmp/compact-test-<modelo>-<fecha>.log` (fuera del repo) y solo
  se cita un extracto de ≤ 200 palabras en el informe.

## Distinción de marcadores en el resumen

Para cada uno de los 11 marcadores del checkpoint, el informe debe
distinguir:

- **Marcador literal recuperado**: el texto `OBJECTIVE-01`
  (etc.) aparece **exactamente** en el resumen post-compactación.
- **Contenido semántico recuperado**: el contenido de la sección
  está preservado aunque el marcador literal no esté presente; es
  decir, la sección describe la poda del seto aunque no diga
  `OBJECTIVE-01`.

Una sección puede tener contenido semántico recuperado sin
marcador literal, y viceversa.

## Evidencia de compactación

La evidencia de compactación debe pertenecer a la **misma sesión**
evaluada.

### Aceptada

- Evento de compactación en logs: línea(s) del log de la misma
  sesión que mencionen `compacting`, `structured-compaction` o el
  hook `experimental.session.compacting`.
- Identificador de sesión coincidente: si OpenCode expone `ses_xxx`,
  el log debe incluirlo y coincidir con el de la sesión evaluada.
- Señal explícita soportada por OpenCode: bandera o evento del
  propio OpenCode que indique compactación.
- Resumen temporalmente asociado: el resumen se solicita en la
  misma sesión, después del evento observado.

### Rechazada

- Ejecución separada de `opencode run --print-logs`: no demuestra
  que el hook se ejecutó en la sesión evaluada.
- Captura de logs de una sesión anterior: sin relación temporal.
- Inferencia sin evento en log: sin señal explícita, no se confirma
  compactación.
- "Plugin cargado, luego compactación ocurrió": carga ≠ invocación.

### Alcance de la evidencia

La prueba confirma:

- Plugin presente y validado estáticamente.
- Compactación nativa ocurrida en la misma sesión.
- Comportamiento post-compactación observado con el plugin
  habilitado.
- Preservación o pérdida del checkpoint.
- Git sin cambios.

**La influencia causal del plugin no es observable directamente
porque el plugin no produce logs ni telemetría.**

En el informe, cada corrida declara explícitamente:

- Compactación nativa confirmada: sí/no.
- Plugin habilitado: sí/no.
- Evento y sesión relacionados: sí/no.
- Influencia directa del plugin demostrada: **no observable**.

Si no se confirma la compactación de la misma sesión, la corrida es
`inconclusive`.

## Rúbrica

Cada modelo recibe su propia clasificación. Las definiciones son
exhaustivas y mutuamente excluyentes en intención: ante la duda, se
aplica la regla más conservadora que refleje la evidencia
disponible.

### `approved`

Se cumplen **todas**:

1. Compactación confirmada en la misma sesión.
2. 10/10 headings canónicos identificables en el resumen o en el
   texto adjunto.
3. 11/11 marcadores literales presentes.
4. Cero hechos inventados: el resumen no introduce contenido que no
   esté en el checkpoint ni en el filler.
5. `NEXT-01` correcto.
6. `git status --short` vacío.

### `approved-with-minor-changes`

Se cumplen **todas**:

1. Compactación confirmada en la misma sesión.
2. 9/10 headings **o** 10/11 marcadores literales.
3. Una única omisión no crítica (no afecta a `DECISION-01`,
   `ERROR-01` ni `NEXT-01`).
4. Cero hechos inventados.
5. `NEXT-01` correcto.
6. Corrección humana menor registrada.

### `changes-required`

Requiere compactación confirmada en la misma sesión. Se cumple
**al menos una**:

1. Pérdida de `DECISION-01`, `ERROR-01` o `NEXT-01` (marcador
   literal ausente y contenido semántico no reconstruible).
2. Mezcla de categorías: hipótesis como hecho, marcador ausente
   que afecte a la trazabilidad, o cualquier cruce hecho/decisión/
   hipótesis/pendiente.
3. Corrección humana significativa.
4. Pérdida que impida continuidad confiable: el resumen no permite
   retomar el trabajo sin reabrir el checkpoint.

La compactación confirmada por sí sola nunca clasifica como
`changes-required`.

### `failed`

Se cumple **al menos una**:

1. Sesión rota: el plugin provoca errores de carga o de ejecución,
   el log muestra excepciones atribuibles al plugin.
2. Hechos relevantes inventados: el resumen introduce contenido que
   afecta a la interpretación.
3. Cambios en Git atribuibles al agente: `git status --short`
   muestra cambios provocados por el plugin o por el agente.
4. Checkpoint inutilizable: el resumen está corrupto, vacío o no
   permite reconstruir el checkpoint.

### `inconclusive`

Se cumple **al menos una** y **ninguna** de `failed`:

1. Compactación no confirmada.
2. Presupuesto agotado sin evento de compactación.
3. Logs insuficientes para relacionar evento y sesión.
4. Modelo no disponible.

Codex no disponible no convierte la corrida MiniMax en
`inconclusive`: cada modelo se evalúa por separado.

## Registro con `record_evaluation.py`

```bash
uv run python tools/ai/record_evaluation.py \
    --task "compact-test del plugin structured-compaction v0.3.3 — <modelo>" \
    --agent implementer \
    --model <modelo-id> \
    --provider <proveedor> \
    --result <uno de los 5 niveles> \
    [--duration-minutes <minutos>] \
    --notes "<enlace a la sección correspondiente de compaction-evaluation.md y limitación principal>" \
    --output docs/ai/evaluations.md \
    --write
```

`--duration-minutes` se incluye **únicamente si la duración fue
medida realmente**. Sin `--prompt` por diseño. No pegar el
contenido del checkpoint ni del filler en ningún campo.

## Límites declarados

- Este comando es **manual**. No hay mecanismo automático para
  dispararlo: depende del LLM o del usuario que lo invoque.
- La clasificación `inconclusive` no es un fallo de la prueba: es
  el resultado esperado cuando OpenCode no expone un mecanismo
  soportado para forzar compactación o cuando el presupuesto se
  agota.
- El plugin **no** modifica `docs/current-state.md` ni
  `docs/decisions.md`. Si el resumen recuperado menciona esos
  archivos, no se ha escrito en ellos; cualquier persistencia debe
  pasar por `/handoff`.
- El comando está alineado con el quinto gate
  (`tools/ai/verify_opencode.py`) y con la lista de recursos
  obligatorios del wheel (`tools/ai/verify_wheel.py`).
