# Evaluaciones de modelos

Registro de evaluaciones concretas de modelos de lenguaje en tareas reales del proyecto. Cada entrada documenta modelo, tarea, resultado, tiempo, correcciones humanas, validaciones y decisión de uso futuro.

No se registran impresiones generales: solo experimentos comparables con una tarea definida y un resultado medible. Una entrada sirve para decidir, en el futuro, qué modelo usar para una tarea parecida.

---

## Plantilla

```markdown
### YYYY-MM-DD — <título corto>

- **Modelo**: id exacto del modelo (por ejemplo `proveedor/modelo-x`).
- **Proveedor**: nombre del proveedor.
- **Interfaz**: interfaz utilizada (por ejemplo OpenCode Web, terminal).
- **Tarea**: descripción concreta de lo que se pidió al modelo.
- **Complejidad**: baja | media | alta.
- **Prompt o entrada**: resumen del prompt o enlace al archivo relevante.
- **Resultado del modelo**: resumen del output y archivos modificados.
- **Tiempo invertido**: estimación del tiempo total de la interacción (incluyendo iteraciones y reintentos).
- **Correcciones humanas**: qué hubo que ajustar manualmente después.
- **Validaciones**: resultado de los quality gates aplicados (`ruff`, `pyright`, `pytest`).
- **Decisión de uso futuro**: repetir con el mismo modelo, escalar a premium, replantear la tarea, etc.
```

---

### 2026-07-23 — Hardening operativo v0.3.0: scripts de CI y verificación del wheel

- **Modelo**: `MiniMax-M3` (`minimax-direct/MiniMax-M3`).
- **Proveedor**: MiniMax.
- **Interfaz**: OpenCode Web.
- **Tarea**: añadir CI reproducible y herramientas locales de verificación
  al repositorio `python-ai-template` sin modificar el comportamiento del
  generador. Entregables: `tools/ai/verify.py` (orquestador de los cuatro
  quality gates), `tools/ai/verify_wheel.py` (verificador del wheel y de
  la consistencia de las cuatro fuentes de versión) y
  `.github/workflows/ci.yml` (pipeline con matriz `quality` en Python 3.12
  y 3.14 y job `package` dependiente con build + verificación + artifact
  único, Actions fijadas por SHA completo).
- **Complejidad**: alta.
- **Prompt o entrada**: conversación de varias iteraciones con
  planificación, correcciones obligatorias del plan original (no
  modificar `.gitignore`, usar las releases estables más recientes de las
  Actions fijadas por SHA completo, AST estático para `__version__`,
  `fail-fast: false`), implementación, revisión independiente y cierre
  documental.
- **Resultado del modelo**:
  - Tres archivos creados y validados en local: `tools/ai/verify.py`
    (89 líneas), `tools/ai/verify_wheel.py` (256 líneas),
    `.github/workflows/ci.yml` (63 líneas).
  - Sin modificaciones a `pyproject.toml`, `uv.lock`, código del
    generador, `tests/`, `.gitignore`, `docs/` previos, `AGENTS.md`
    previo, configuración de OpenCode ni shim local.
  - Pipeline de CI ejecutada y aprobada en GitHub Actions (run
    `30041232754`).
- **Tiempo invertido**: varias sesiones interactivas con iteraciones de
  planificación, correcciones técnicas del plan, implementación,
  revisión y cierre documental.
- **Correcciones humanas**:
  - Eliminación de la propuesta de tocar `.gitignore` para
    `tools/ai/__pycache__/` (la regla global ya cubría el caso).
  - Sustitución de las versiones `@v4/@v6/@v4` de las Actions por las
    releases estables más recientes (`@v7.0.1/@v8.1.0/@v7.0.1`) fijadas
    por SHA completo de 40 caracteres, con el tag como comentario.
  - Cambio de `fail-fast: true` a `fail-fast: false` en la matriz
    `quality` para no perder el diagnóstico de la otra versión cuando
    una falla.
  - Sustitución de la importación dinámica de `python_ai_template` por
    extracción estática con `ast` en `verify_wheel.py` (sin importar ni
    ejecutar el módulo).
  - Forzado de `subprocess.run` con lista, sin `shell=True`, sin
    `capture_output`, salida en vivo, `main() -> int` y
    `raise SystemExit(main())` en `verify.py`.
- **Validaciones**:
  - `uv run ruff check .`: pass.
  - `uv run ruff format --check .`: pass.
  - `uv run pyright`: pass (0 errores, 0 warnings, 0 informations).
  - `uv run pytest`: 33 passed.
  - `uv run python tools/ai/verify.py`: pass (exit 0, los cuatro gates
    en verde).
  - `rm -rf dist && uv build && uv run python tools/ai/verify_wheel.py`:
    pass (exit 0, cuatro fuentes de la versión coinciden, cinco recursos
    obligatorios presentes).
  - CI remoto (run `30041232754`): `quality` 3.12 pass, `quality` 3.14
    pass, `package` pass, artifact `dist` subido (91715 bytes, no
    expirado).
- **Revisión independiente**: aprobada con dos hallazgos menores
  cosméticos (paréntesis redundantes en `REQUIRED_RESOURCES` y
  duplicación de mensaje en una ruta de `verify_wheel.py`) y observaciones
  de compatibilidad futura, sin bloqueantes.
- **Decisión de uso futuro**: el modelo `MiniMax-M3` ha demostrado
  capacidad adecuada para tareas de implementación media-alta sobre
  Python cuando el usuario revisa el plan y corrige desviaciones técnicas
  (compatibilidad de Actions, análisis estático, contrato de `subprocess`,
  separación de jobs). Para esta categoría de trabajo la supervisión
  humana es **necesaria** en: diseño de Actions de GitHub, contrato de
  `subprocess`, parsing estático con `ast`, y separación de jobs
  matrix/no-matrix. Se mantiene en el modelo diario. No se escala a
  premium para esta tarea porque la calidad entregada fue suficiente con
  las correcciones humanas ya incorporadas.

### 2026-07-23 — Capa de exploración y compactación v0.3.1 (scout, /review, context-handoff, structured-compaction)

- **Modelo**: `MiniMax-M3` (`minimax-direct/MiniMax-M3`).
- **Proveedor**: MiniMax.
- **Interfaz**: OpenCode 1.18.4 (CLI + plugin autodescubierto desde `.opencode/plugins/`).
- **Tarea**: añadir una capa de exploración y compactación al
  repositorio `python-ai-template` sin modificar el comportamiento
  del generador ni introducir dependencias de runtime. Entregables:
  (a) agente `scout` de solo lectura en
  `.opencode/agents/scout.md`; (b) comando `/review` manual en
  `.opencode/commands/review.md`; (c) skill `context-handoff` en
  `.opencode/skills/context-handoff/SKILL.md` con el formato
  canónico de diez secciones obligatorias; (d) plugin
  `structured-compaction` en
  `.opencode/plugins/structured-compaction.ts` registrado en el
  hook `experimental.session.compacting` y que añade una sola
  entrada compacta a `output.context` (sin tocar `output.prompt`,
  sin escribir archivos, sin usar red, `BunShell` ni logs
  permanentes); (e) bump de versión `0.3.0` → `0.3.1`; (f)
  alineación de `/handoff` con el formato canónico; (g) registro de
  ADR-012; (h) actualización de
  `AGENTS.md`, `docs/architecture.md`,
  `docs/ai/context-policy.md`, `docs/todos.md` y este registro.
- **Complejidad**: alta (involucra tipos y firmas reales de un SDK
  externo, restricciones del hook experimental, formato canónico
  nuevo y validación sin `tsc`/`npx`).
- **Prompt o entrada**: conversación de varias iteraciones con
  planificación, decisiones explícitas del usuario (no modificar
  `output.prompt`, no usar `tsc`/`npx`/`BunShell`/`tui.d.ts`,
  `/review` manual, contrato de scout en nueve secciones, contrato
  del plugin en ocho secciones, diez secciones obligatorias para
  handoff), implementación, validación y cierre documental.
- **Resultado del modelo**:
  - Cuatro archivos creados y validados:
    - `.opencode/agents/scout.md` (nuevo).
    - `.opencode/commands/review.md` (nuevo).
    - `.opencode/skills/context-handoff/SKILL.md` (nuevo).
    - `.opencode/plugins/structured-compaction.ts` (nuevo;
      **estrictamente estático**, tipado como `Plugin` de
      `@opencode-ai/plugin` 1.18.4, importa únicamente el tipo
      `Plugin` y añade una sola cadena literal a `output.context`).
  - Once archivos modificados: `pyproject.toml`,
    `src/python_ai_template/__init__.py`, `uv.lock`,
    `AGENTS.md`, `.opencode/commands/handoff.md`,
    `.opencode/commands/review.md`,
    `.opencode/skills/context-handoff/SKILL.md`,
    `docs/architecture.md`, `docs/ai/context-policy.md`,
    `docs/decisions.md`, `docs/todos.md`, `docs/current-state.md`,
    `docs/ai/evaluations.md`. `opencode.jsonc` se mantuvo intacto:
    la verificación confirmó que `.opencode/plugins/*.ts` se
    autodescubre sin necesidad de declararlo.
  - Sin cambios en `src/python_ai_template/` (más allá del bump
    de `__version__`), `tests/`, `tools/`, `tools/ai/`,
    `.github/workflows/ci.yml`, `docs/glossary.md`,
    `docs/mistakes.md`, `README.md`, `tools/new_project.py`. El
    comportamiento del generador es idéntico al de v0.3.0.
- **Tiempo invertido**: varias sesiones interactivas con iteraciones
  de planificación, decisiones explícitas del usuario, primera
  revisión interna (veredicto "Requiere cambios"), implementación
  de las correcciones, segunda revisión y cierre documental.
- **Correcciones humanas**:
  - Tras la primera revisión: refactorización del plugin para
    eliminar toda lectura de `docs/current-state.md` y
    `pyproject.toml`. La versión revisada del plugin es
    estrictamente estática (sin `node:fs`, sin `node:path`, sin
    `readFile`, sin extracción de Markdown, sin regex de
    `pyproject.toml`, sin valores `(no leído en esta sesión)`).
    El plugin importa únicamente el tipo `Plugin` desde
    `@opencode-ai/plugin` y añade una sola cadena literal a
    `output.context`.
  - Corrección del header `## Siguiente acción concreta` en
    `docs/current-state.md` (faltaba la tilde en `acción`) y
    reescritura sistemática del archivo en UTF-8 con tildes
    correctas, manteniendo los hechos verificables del bloque de
    trabajo.
  - Ampliación de `/review` con un chequeo explícito de plugins
    de compactación: no escriben archivos, no leen archivos vía
    filesystem, no usan shell, no llaman a la red, no generan
    logs permanentes, no modifican `output.prompt` y sólo agregan
    contexto auxiliar a `output.context`.
  - Corrección del `scout` para usar exactamente las nueve
    secciones del contrato del usuario (objetivo interpretado,
    hechos verificados, flujo actual, decisiones aplicables,
    riesgos, hipótesis, preguntas abiertas, archivos que
    probablemente requerirían cambios, siguiente lectura
    recomendada), en lugar del formato libre inicial.
  - Realineación de `/review` con los cuatro veredictos
    permitidos (`Aprobado`, `Aprobado con cambios menores`,
    `Requiere cambios`, `Rechazado`) y las ocho secciones del
    formato de salida.
  - Migración de `context-handoff` y `docs/ai/context-policy.md`
    a las diez secciones del formato canónico (incluidas las dos
    nuevas: "Hechos verificados" y "Divergencias detectadas").
  - Confirmación empírica de que `opencode debug config` registra
    el plugin con `scope: "local"` desde `.opencode/plugins/`, lo
    que evitó modificar `opencode.jsonc`.
  - Sustitución del intento inicial de usar `npx tsc` por greps
    de validación sobre el plugin, alineados con la regla del
    usuario de no añadir herramientas temporales.
- **Validaciones estáticas** (comprobaciones sobre archivos y
  configuración, sin ejecutar el repositorio):
  - Inspección directa del código de
    `.opencode/plugins/structured-compaction.ts` (125 líneas):
    importa únicamente `import type { Plugin } from
    "@opencode-ai/plugin"` (línea 49, type-only); declara
    `STATIC_COMPACTION_REMINDER` como constante literal; registra
    únicamente el hook `experimental.session.compacting`; el
    callback realiza una sola operación
    `output.context.push(STATIC_COMPACTION_REMINDER)` (línea 122);
    no asigna `output.prompt` (la única mención del identificador
    está en el docstring, línea 12, como documentación de la
    promesa, no como código).
  - `grep -nE "node:fs|node:path|readFile|writeFile|readdir|stat\(" .opencode/plugins/structured-compaction.ts`:
    cero coincidencias.
  - `grep -c "output.context.push" .opencode/plugins/structured-compaction.ts`:
    `1`.
  - `grep '^## ' docs/current-state.md`: los diez encabezados
    canónicos literales en orden.
  - Revisión de `opencode.jsonc`: intacto (sin cambios en esta
    unidad); plugin autodescubierto por OpenCode 1.18.4 desde
    `.opencode/plugins/` con `scope: "local"`.
  - `git diff --check`: pass.
  - `git status --short`: 11 archivos modificados + 4 untracked en
    el momento del cierre de la corrección.
  - `git diff --stat`: único cambio "no esperado" en superficie es
    el bump de `uv.lock` que `uv` aplica al detectar el cambio de
    `pyproject.toml`.
- **Validaciones funcionales** (ejecutores reales corridos en esta
  sesión):
  - `uv run ruff check .`: pass.
  - `uv run ruff format --check .`: pass.
  - `uv run pyright`: pass (`0 errors, 0 warnings, 0 informations`).
  - `uv run pytest`: pass (`33 passed`).
  - `uv run python tools/ai/verify.py`: pass (los cuatro gates en
    verde, exit 0).
  - `rm -rf dist && uv build`:
    `python_ai_template-0.3.1-py3-none-any.whl`,
    `python_ai_template-0.3.1.tar.gz`.
  - `uv run python tools/ai/verify_wheel.py`: pass (cuatro
    fuentes de la versión coinciden en `0.3.1`; cinco recursos
    obligatorios presentes).
  - **Sesión interactiva con el agente `scout`** sobre el empaquetado
    del template y la validación del wheel. Identificó correctamente
    `generator.py`, `template/`, `pyproject.toml`, `verify_wheel.py`
    y `ci.yml`; explicó el flujo Hatchling -> `package data` ->
    `importlib.resources` -> `verify_wheel.py` -> job `package`;
    separó hechos, riesgos, hipótesis y preguntas abiertas según su
    contrato de nueve secciones; no modificó archivos. Observación:
    la respuesta fue correcta pero más extensa de lo deseable para
    el perfil compacto del scout.
  - **Ejecución interactiva de `/review`** sobre el diff de la
    unidad. Veredicto: **Aprobado con cambios menores**. Sin
    bloqueantes ni mayores. Cuatro hallazgos menores: (1) deriva
    histórica de `docs/todos.md` sobre v0.3.0; (2) permisos
    heterogéneos en `.opencode/agents/`; (3) validación estática
    del plugin no incorporada a CI; (4) IDs de sesión demasiado
    específicos en `docs/current-state.md`.
  - Carga del plugin por OpenCode 1.18.4:
    - `opencode --version`: `1.18.4`.
    - `opencode debug config`: el plugin aparece en `plugin_origins`
      con `scope: "local"` desde
      `file:///home/giuseppe/projects/python-ai-template/.opencode/plugins/structured-compaction.ts`.
    - `opencode run --print-logs --log-level INFO --format json`:
      crea la sesión `ses_06f29e98bffeJ55fPuQMKLnl4U` (primera
      prueba) y `ses_06f1aa6dcffeyMi1xpOBP4ZJT2` (segunda prueba
      tras la corrección) con `version=1.18.4`, sin errores de
      carga del plugin.
- **Validaciones funcionales pendientes** (no ejecutadas en esta
  sesión; deben ejecutarse en una sesión interactiva real o al
  empujar los commits):
  - Compactación real disparada por umbral en OpenCode 1.18.4 (la
    carga del plugin se verificó en una sesión real corta; la
    compactación real no se provocó).
  - Sesión limpia de reconstrucción de contexto al inicio de una
    sesión nueva en un árbol de trabajo fresco.
  - CI remota (run GitHub Actions); los cambios no están en `main`
    ni han sido empujados por el usuario.
- **Revisión independiente**: aprobada tras la corrección de los
  hallazgos bloqueantes (acento faltante en el header) y mayores
  (uso de filesystem por el plugin; ausencia de chequeo de
  filesystem en `/review`). La sesión interactiva real de `/review`
  emitió el veredicto **Aprobado con cambios menores** (cuatro
  hallazgos menores documentados en el informe). Las dos rondas de
  revisión previas y la interactiva se documentan en esta evaluación
  y en `docs/current-state.md`.
- **Decisión de uso futuro**: el modelo `MiniMax-M3` ha demostrado
  capacidad adecuada para integrar tipos de un SDK externo
  (`@opencode-ai/plugin` 1.18.4) cuando el usuario proporciona los
  contratos exactos y las restricciones (no `tsc`, no `npx`,
  contrato de secciones, ausencia de secretos y de escritura en el
  plugin, plugin estrictamente estático). La supervisión humana
  sigue siendo necesaria para: alinear el plugin con los hooks
  experimentales, ajustar el formato de las secciones canónicas,
  validar el formato del handoff a la primera iteración, y detectar
  regresiones cuando el plugin introduce dependencias dinámicas
  no autorizadas por el contrato. Se mantiene en el modelo diario.
  Las sesiones interactivas reales (scout, /review) confirmaron que
  ambos artefactos responden a su contrato documentado sin
  regresiones. El scout mostró una tendencia a respuestas más
  extensas de lo compacto esperado; si persiste, evaluar un límite
   de extensión explícito en su archivo de agente.

### 2026-07-23 — Sesión limpia reducida de reconstrucción de contexto (v0.3.1)

- **Modelo**: `opencode/deepseek-v4-flash-free`.
- **Proveedor**: OpenCode / DeepSeek.
- **Interfaz**: OpenCode Web.
- **Tarea**: reconstruir el estado del proyecto desde cero en una
  sesión nueva (tras cambiar de modelo por agotamiento de cuota en
  la ejecución anterior), leyendo únicamente `AGENTS.md`,
  `docs/current-state.md`, `git status --short` y
  `git log --oneline -3`, sin modificar archivos.
- **Complejidad**: baja (tarea acotada de lectura y reconstrucción).
- **Prompt o entrada**: instrucción de reconstruir el estado actual
  leyendo solo los cuatro recursos enumerados, máximo 400 palabras,
  sin escribir archivos.
- **Resultado del modelo**: reconstruyó correctamente objetivo v0.3.1,
  11 archivos modificados + 4 untracked, último commit `49dfcde`,
  plugin estático y experimental, quality gates y wheel aprobados,
  CI remota pendiente, compactación real pendiente. Sin texto
  corrupto ni invenciones.
- **Tiempo invertido**: una sola interacción.
- **Correcciones humanas**: ninguna.
- **Validaciones**: no aplican quality gates de código (tarea de solo
  lectura). La salida fue revisada visualmente: no hay texto corrupto,
  los hechos citados coinciden con el estado real del repositorio.
- **Decisión de uso futuro**: la sesión limpia reducida funciona como
  validación de continuidad mínima. La variante ampliada (con
  `docs/architecture.md` y ADR) queda como opcional, no como bloqueo.
  El modelo es adecuado para tareas de reconstrucción acotada de
  contexto siempre que se limiten explícitamente los documentos a
  leer para evitar deriva. La ejecución anterior con el mismo modelo
  (DeepSeek V4 Flash Free) produjo salida corrupta tras agotamiento
  de cuota, por lo que no se considera evidencia válida; esta
  ejecución sí lo es.

### 2026-07-23 — Implementar v0.3.2: validacion estatica de OpenCode y línea

- **Modelo**: `opencode/deepseek-v4-flash-free`.
- **Proveedor**: `OpenCode / DeepSeek`.
- **Agente**: `implementer`.
- **Tarea**: Implementar v0.3.2: validacion estatica de OpenCode y linea base de evaluacion.
- **Resultado**: `approved-with-minor-changes`.
- **Duración**: 90.0 minutos.
- **Escalado**: no.
- **Correcciones**: tras la primera entrega, el usuario pidio correcciones obligatorias antes de /review: auditoria root<->template, politica canonica de distribucion (template como fuente), sync obligatorio, 7 recursos OpenCode en el wheel, tests E2E en test_new_project, y no cerrar la unidad en docs/todos.md hasta /review + bump + CI + tag. Todas aplicadas.
- **Notas**: ADR-013, sin telemetria externa, sin routing, sin dependencias de runtime. Quinto gate integrado, registrador manual creado, prueba controlada compact-test documentada, presupuesto contractual del scout anadido. Tests hermeticos en tmp_path. La unidad NO esta cerrada todavia (ver docs/todos.md "En revision").

### 2026-07-23 — v0.3.2 en revision: sync root<->template anadido, 7 recursos

- **Modelo**: `opencode/deepseek-v4-flash-free`.
- **Proveedor**: `OpenCode / DeepSeek`.
- **Agente**: `implementer`.
- **Tarea**: v0.3.2 en revision: sync root<->template anadido, 7 recursos OpenCode exigidos en wheel.
- **Resultado**: `approved-with-minor-changes`.
- **Duración**: 30.0 minutos.
- **Escalado**: no.
- **Correcciones**: ninguna
- **Notas**: Sincronizacion root<->template implementada (politica: template canonico). verify_opencode.py ampliado con verify_sync. verify_wheel.py ampliado a 12 recursos (5 originales + 7 de la capa OpenCode). Tests E2E para new_project ampliados. Sin bump todavia. Conteo real de tests por archivo (verificado con `pytest --collect-only -q`): tests/test_new_project.py: 35; tests/test_record_evaluation.py: 29; tests/test_verify_opencode.py: 43; tests/test_verify_wheel.py: 8; total: 115.

### 2026-07-23 — Correcciones finales v0.3.2: 8/8, repo_root robusto, evaluación atómica

- **Modelo**: `opencode/deepseek-v4-flash-free`.
- **Proveedor**: `OpenCode / DeepSeek`.
- **Agente**: `implementer`.
- **Tarea**: Correcciones finales v0.3.2 antes del bump: resumen 8/8, repo_root sin cwd, tests de heading incorrecto y node:http, evaluación atómica con try/finally.
- **Resultado**: `approved-with-minor-changes`.
- **Duración**: no registrada.
- **Escalado**: no.
- **Correcciones**: se corrigieron dos falsos positivos del /review previo: (1) el heading con `# ` (nivel 1) **ya fallaba** por ausencia en la lista de `## `, se añadió test hermético; (2) el job `package` de CI **ya ejecuta** `verify_wheel.py`, no requiere activación manual. Se añadieron tests de interrupción (KeyboardInterrupt) y fallo en `append_entry`. Se renombró la resolución de raíz a función pública `resolve_repo_root()` para cumplir pyright strict. Queda v0.3.2 "En revisión" como especifica el plan de cierre.
- **Notas**: verify_opencode.py ahora usa `TOTAL_OK_CHECKS = 8` y `resolve_repo_root()` desde `Path(__file__).resolve().parents[2]`. `append_entry` usa `try/finally` en lugar de `except/raise` para cubrir KeyboardInterrupt. Total de tests: 121 (35+31+47+8).

### 2026-07-23 — Validación final v0.3.2 desde tag remoto

- **Modelo**: `opencode/deepseek-v4-flash-free`.
- **Proveedor**: `OpenCode / DeepSeek`.
- **Agente**: `implementer`.
- **Tarea**: Cierre remoto de v0.3.2: validar CI, tag, instalación desde tag y distribución de 7 artefactos OpenCode.
- **Resultado**: `approved`.
- **Duración**: no registrada.
- **Escalado**: no.
- **Correcciones**: ninguna
- **Notas**: CI run `30058735050` con jobs quality 3.12, quality 3.14 y package aprobados. Tag `v0.3.2` publicado y apunta a `f063fe2`. Instalación desde tag remoto validada: `new-python-project --version` devuelve `0.3.2`, `--help` funciona, proyecto temporal generado contiene los 7 artefactos OpenCode distribuidos (scout, compact-test, handoff, review, verify, structured-compaction.ts, context-handoff/SKILL.md). Herramienta desinstalada correctamente. Compactación real por umbral sigue experimental y no se verificó en esta sesión. v0.3.2 cerrada.
