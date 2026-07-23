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
