# Errores recurrentes

Registro de errores recurrentes o con valor futuro. Cada entrada documenta síntoma, causa raíz, corrección y prevención para evitar que se repita.

No se registran errores triviales: ni typos de una vez, ni descuidos puntuales sin patrón, ni errores que no se repetirán. Solo se documenta lo que aporta aprendizaje futuro. El comando `/mistake` aplica este filtro.

---

## Plantilla

```markdown
### YYYY-MM-DD — <título corto>

- **Síntoma**: cómo se manifestó el problema.
- **Causa raíz**: por qué ocurrió, con referencia a archivos o comandos si aplica.
- **Corrección**: qué se cambió para resolverlo.
- **Prevención**: regla, validación, checklist o automatización que evite la repetición.
```

---

### 2026-07-23 — `pyproject.toml` generado usaba el nombre visible como nombre de distribución

- **Síntoma**: la generación con

  ```bash
  --name "E2E Smoke"
  --package e2e_smoke
  ```

  producía en el `pyproject.toml` del proyecto generado:

  ```toml
  [project]
  name = "E2E Smoke"
  ```

  `uv sync` rechazaba el proyecto con un error de metadatos: el nombre de
  distribución no admite espacios.

- **Causa raíz**: se reutilizó `{{PROJECT_NAME}}`, que es un nombre
  **visible**, como nombre técnico de distribución en `[project].name`. Los
  tests verificaban la sustitución textual del placeholder y la estructura
  del árbol generado, pero no validaban la semántica real del proyecto
  generado mediante `uv sync`. Mientras no se ejecuta `uv sync` dentro del
  proyecto generado con datos representativos, este tipo de error pasa los
  tests unitarios.

- **Corrección**: se introdujo un tercer placeholder, `{{DISTRIBUTION_NAME}}`,
  derivado internamente de `{{PACKAGE_NAME}}` mediante:

  ```text
  e2e_smoke -> e2e-smoke
  ```

  La derivación es `package_name.lower().replace("_", "-")` y el resultado se
  valida con la expresión regular:

  ```text
  ^[a-z0-9]+(?:-[a-z0-9]+)*$
  ```

  Si no cumple el patrón, el generador falla antes de escribir. La
  sustitución en `template/pyproject.toml.tmpl` usa
  `{{DISTRIBUTION_NAME}}` para `[project].name`, mientras que las rutas,
  imports y configuración de paquetes siguen usando `{{PACKAGE_NAME}}`. La
  distinción entre los tres nombres se documenta en ADR-008.

- **Prevención**: un generador no se considera terminado hasta:

  1. generar un proyecto independiente con el generador;
  2. usar datos representativos, incluyendo un nombre visible con espacios;
  3. ejecutar dentro del proyecto generado:
     - `uv sync`
     - `uv run ruff check .`
     - `uv run ruff format --check .`
     - `uv run pyright`
     - `uv run pytest`

  Los tests unitarios del generador son necesarios pero **no sustituyen** el
  E2E semántico. La regla queda incorporada a la definición de terminado de
  esta plantilla.

---

### 2026-07-30 — Runaway loop por detección tardía de no-progress / mismo fingerprint

- **Síntoma**: el simulador de bounded execution loop no detectaba a tiempo que
  una misma acción se repetía sin progreso, permitiendo iteraciones fantasma
  que consumían presupuesto sin avanzar. En concreto: la regla de finalización
  comparaba `expected_state_change` con `state_after` y declaraba la fase
  completada sin señal explícita (`completes_phase`), y el límite de
  no-progress usaba `>` en vez de `>=`.
- **Causa raíz**: el contrato original carecía de un flag explícito
  (`completes_phase`) para distinguir "avance dentro de la fase" de "fase
  completada". Además, el orden de evaluación en `run_step` priorizaba la
  idempotencia del estado terminal sobre la detección de reinicio de fase
  completada, dando lugar a que un `COMPLETED` fuese idempotente en vez de
  producir `BLOCKED_LOOP`.
- **Corrección**:
  - Se introdujo `StepOutcome.completes_phase: bool` (default `False`).
  - Se cambió el orden de reglas: reinicio de fase completada se evalúa
    antes que idempotencia.
  - `COMPLETED` requiere `outcome.success and progress and outcome.completes_phase`.
  - `no_progress_count >= DEFAULT_MAX_NO_PROGRESS` usa `>=` en vez de `>`.
  - Se añadieron tests 9 y 10 para verificar casos límite de `completes_phase`.
- **Prevención**: el simulador en `tests/test_bounded_loop.py` es la
  validación contractual. Cualquier cambio en las reglas del loop debe
  mantener los 22 tests actuales (10 escenarios + 7 invariantes + 5
  resource_limit).

### 2026-07-30 — Provider resource exhaustion sin manejo explícito en el contrato

- **Síntoma**: la interrupción por límite de cuota del proveedor (token plan
  exhausted) no tenía representación en el contrato bounded-loop. Al ocurrir,
  el worker no podía distinguir entre un fallo normal y un agotamiento de
  recurso externo reanudable.
- **Causa raíz**: el contrato original modelaba `ESCALATED` como "el worker
  juzgó que requiere un humano", pero no cubría el caso específico de límite
  de recurso del proveedor, que es reanudable con distinto modelo y requiere
  sanitización del mensaje.
- **Corrección**: se modeló `ResourceLimit` como evento genérico (independiente
  de proveedor: DeepSeek, MiniMax, OpenAI, etc.) con campos `provider`,
  `model`, `limit_kind`, `raw_message` (sanitizado), `tool_calls_used`,
  `step_number`, `checkpoint_available` y `resumable`. La función
  `handle_resource_limit` produce `ESCALATED` con razón documentada y mensaje
  sanitizado.
- **Prevención**:
  - `resource_limit → ESCALATED` (agotamiento de plan/cuota externo), no
    confundir con `runaway_loop → BLOCKED_LOOP` (misma acción repetida
    sin progreso).
  - No atribuir causalidad al proveedor sin evidencia: `ResourceLimit` es
    genérico y no presume qué proveedor lo causó.
  - Los 5 tests de `ResourceLimit` en `tests/test_bounded_loop.py` verifican:
    token exhausto → ESCALATED, checkpoint disponible, no acciones posteriores,
    reanudabilidad, y sanitización de credenciales.
