# Decisiones arquitectónicas (ADR)

Registro de decisiones arquitectónicas del proyecto. Cada entrada sigue el formato ADR ligero: ID, fecha, contexto, decisión, alternativas, consecuencias, reversibilidad, estado.

Las decisiones no se modifican silenciosamente. Una corrección se hace añadiendo una nueva entrada que referencia y corrige la anterior.

## ADR-001: el repositorio es la fuente de verdad

- **Fecha**: 2026-07-23
- **Estado**: aceptada.
- **Contexto**: con múltiples agentes y herramientas (OpenCode, ChatGPT Codex, futuros agentes) hay riesgo de divergencia entre el código, la documentación interna y los resúmenes externos o la memoria del modelo.
- **Decisión**: el repositorio, su código, su configuración vigente y `docs/` son la fuente de verdad operativa. Cualquier resumen externo debe poder contrastarse con el repo.
- **Alternativas consideradas**:
  - Confiar en resúmenes externos: descartado por riesgo de desfase.
  - Mantener un wiki externo: descartado por duplicación y desactualización inevitable.
- **Consecuencias**: los agentes deben consultar `docs/current-state.md` y los archivos relevantes al inicio de cada sesión, y contrastar contra el código cuando haya divergencia. `docs/ai/context-policy.md` formaliza esta práctica.
- **Reversibilidad**: fácil. Basta con revisar las prácticas y los documentos.

## ADR-002: OpenCode es el agente cotidiano

- **Fecha**: 2026-07-23
- **Estado**: aceptada.
- **Contexto**: se necesita una interfaz cotidiana consistente para trabajo de implementación y revisión dentro del repositorio, sin acoplarse a un editor o servicio concreto.
- **Decisión**: OpenCode es el agente cotidiano. La configuración se reparte entre `~/.config/opencode/opencode.json` (global) y `opencode.jsonc` (proyecto).
- **Alternativas consideradas**:
  - Trabajar solo con la terminal y editores externos: descartado por falta de asistencia estructurada.
  - Usar una herramienta distinta por sesión: descartado por inconsistencia operativa.
- **Consecuencias**: las definiciones de agentes, comandos y skills viven en `.opencode/`. La documentación operativa del proyecto asume OpenCode como punto de partida.
- **Reversibilidad**: difícil. Migrar a otra herramienta implica reescribir la capa de automatización.

## ADR-003: el modelo diario se configura en el global de OpenCode

- **Fecha**: 2026-07-23
- **Estado**: aceptada.
- **Contexto**: el trabajo cotidiano requiere un modelo con buena relación calidad/costo y una configuración consistente.
- **Decisión**: el modelo diario se configura en `~/.config/opencode/opencode.json`. El proyecto no duplica modelo, provider ni API key.
- **Alternativas consideradas**:
  - Configurar varios modelos según tarea desde el inicio: pospuesto; se hará explícito cuando la evidencia lo justifique.
  - Usar un modelo local: descartado por requisitos de hardware y consistencia.
- **Consecuencias**: el proyecto no duplica modelo, provider ni API key; hereda la configuración global. `opencode.jsonc` no incluye claves ni proveedores.
- **Reversibilidad**: fácil. Cambiar el modelo en la configuración global aplica a todo el entorno.

## ADR-004: existe una vía de escalamiento premium

- **Fecha**: 2026-07-23
- **Estado**: aceptada.
- **Contexto**: hay tareas que requieren mayor capacidad de razonamiento (arquitectura, migraciones amplias, debugging complejo, seguridad, cambios difíciles de revertir).
- **Decisión**: se reserva una vía de escalamiento premium para esas tareas. Se invoca solo cuando el modelo diario no alcanza después de al menos dos ciclos razonables de intento.
- **Alternativas consideradas**:
  - Usar el modelo premium por defecto: descartado por costo y por preferir desarrollo cotidiano más económico.
  - No tener vía de escalamiento: descartado por riesgo de quedarse atascado en tareas complejas.
- **Consecuencias**: las decisiones sobre qué modelo usar en cada tarea se rigen por `docs/ai/model-policy.md`. Cada escalamiento se registra en `docs/ai/evaluations.md`.
- **Reversibilidad**: fácil. Cambiar la política o el modelo de escalamiento solo requiere actualizar los documentos.

## ADR-005: uv es el gestor Python canónico

- **Fecha**: 2026-07-23
- **Estado**: aceptada.
- **Contexto**: se necesita un gestor de dependencias reproducible, rápido y que no requiera herramientas globales adicionales.
- **Decisión**: `uv` es el gestor Python canónico. Todas las herramientas (`ruff`, `pyright`, `pytest`) se invocan a través de `uv run`.
- **Alternativas consideradas**:
  - `pip` + `venv`: descartado por fricción y lentitud.
  - `poetry` o `pdm`: descartado por dependencia adicional y por no aportar más valor que `uv` para este proyecto.
- **Consecuencias**: el repositorio asume `uv` instalado en el sistema. La calidad se valida con `uv run <herramienta>`. `README.md` y `AGENTS.md` documentan los comandos en esa forma.
- **Reversibilidad**: difícil. Migrar a otro gestor implica reescribir `pyproject.toml` y los comandos documentados.

## ADR-006: OpenCode Web es la interfaz humana principal

- **Fecha**: 2026-07-23
- **Estado**: aceptada.
- **Contexto**: la persona a cargo del proyecto necesita una interfaz estable para trabajar con agentes sin acoplarse a un editor o dispositivo específico.
- **Decisión**: OpenCode Web es la interfaz humana principal. La configuración de proyecto en `opencode.jsonc` se diseña pensando en esa interfaz.
- **Alternativas consideradas**:
  - Acoplarse a un editor concreto: descartado para mantener portabilidad.
  - Usar solo terminal: descartado por pérdida de asistencia estructurada y de comandos slash.
- **Consecuencias**: los comandos (`/verify`, `/handoff`, `/decision`, `/mistake`) se invocan desde esa interfaz. La configuración debe ser portable a otras interfaces compatibles con OpenCode.
- **Reversibilidad**: media. Cambiar la interfaz puede requerir ajustes menores de configuración y de los comandos documentados.

## ADR-007: ningún cambio se considera terminado sin quality gates

- **Fecha**: 2026-07-23
- **Estado**: aceptada.
- **Contexto**: la calidad del código Python debe ser verificable de forma automática y reproducible. Sin esta condición, las regresiones se acumulan silenciosamente.
- **Decisión**: ningún cambio se considera terminado sin pasar `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright` y `uv run pytest`. Esta condición forma parte de la definición de terminado en `AGENTS.md`.
- **Alternativas consideradas**:
  - Validación manual: descartada por inconsistencia.
  - Validación opcional: descartada por permitir regresiones silenciosas.
  - Relajar controles para que pasen (noqa, ignores amplios, tests saltados): prohibido explícitamente por `AGENTS.md`.
- **Consecuencias**: el comando `/verify` aplica esta regla y bloquea cualquier intento de relajar controles para que las validaciones pasen. Las decisiones sobre cambios en la configuración de los quality gates requieren una nueva ADR.
- **Reversibilidad**: fácil, pero requeriría una nueva ADR que la reemplace.

## ADR-008: el repositorio implementa una plantilla generadora con tres nombres

- **Fecha**: 2026-07-23
- **Estado**: aceptada.
- **Contexto**: el repositorio debe servir como base portable para crear proyectos Python nuevos compatibles con el stack de desarrollo asistido por IA. Cada proyecto nuevo debe heredar la operativa (`AGENTS.md`, `docs/`, `.opencode/`) y las herramientas canónicas (`uv`, `ruff`, `pyright`, `pytest`) sin tener que reescribirlas. La generación E2E detectó que el nombre visible y el nombre de distribución no son el mismo concepto: el primero puede llevar espacios y se usa en textos visibles; el segundo debe cumplir el patrón PEP 503/508 y se usa en `[project].name`.
- **Decisión**: el repositorio entrega una **plantilla generadora** que distingue tres conceptos:
  - **`{{PROJECT_NAME}}`** — nombre visible entregado vía `--name`. Puede
    contener espacios. Se usa en `README.md`, en los docstrings visibles y
    en los textos de la documentación. No se normaliza.
  - **`{{PACKAGE_NAME}}`** — nombre importable entregado vía `--package`.
    Debe ser `str.isidentifier()`, no keyword de Python, solo ASCII, y no
    puede contener puntos, guiones, espacios ni separadores de ruta. Se usa
    en `src/<paquete>/`, en los imports y en la configuración de paquetes
    (`[tool.hatch.build.targets.wheel] packages`).
  - **`{{DISTRIBUTION_NAME}}`** — nombre técnico derivado internamente de
    `{{PACKAGE_NAME}}` mediante `package_name.lower().replace("_", "-")`.
    El resultado se valida con la expresión regular
    `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Si no cumple el patrón, el generador
    falla antes de escribir. Se usa exclusivamente en `[project].name` de
    `pyproject.toml`. No es un argumento CLI: el usuario nunca lo entrega
    directamente.

  El árbol de la plantilla vive en `template/`, con esos tres placeholders
  y un directorio `__package_name__` que se renombra al nombre del paquete.
  El generador `tools/new_project.py` se implementa solo con la biblioteca
  estándar y produce un proyecto independiente por invocación.
- **Alternativas consideradas**:
  - **Usar `{{PROJECT_NAME}}` directamente en `[project].name`**:
    descartada porque los nombres visibles pueden contener espacios y
    `uv sync` rechaza ese valor como nombre de distribución. Es el defecto
    que motiva esta ADR.
  - **Derivar el nombre de distribución desde `{{PROJECT_NAME}}`**:
    descartada porque requeriría una slugificación ambigua (qué hacer con
    mayúsculas, acentos, separadores, caracteres no ASCII). Acoplaría el
    nombre técnico a decisiones de presentación.
  - **Solicitar un cuarto argumento CLI para el nombre de distribución**:
    descartada por complejidad innecesaria. El nombre de distribución es
    una función determinista del nombre del paquete y debe poder derivarse
    sin intervención del usuario. Si en el futuro se necesita un nombre de
    distribución distinto del derivado, la ADR correspondiente deberá
    justificar por qué la derivación por defecto no basta.
  - **Mantener el repositorio como proyecto de ejemplo y copiar a mano**:
    descartada por error humano y por difícil de mantener.
  - **Adoptar Copier o Cookiecutter**: descartada por dependencia externa
    innecesaria para una plantilla tan pequeña.
  - **Hacer que la plantilla sea el propio repositorio (in-place)**:
    descartada por riesgo de mezclar estado heredado con estado nuevo.
- **Consecuencias**: el repositorio no entrega un paquete instalable.
  `pyproject.toml` declara `[tool.uv] package = false` para que `uv sync`
  no intente construir un wheel del repositorio generador. La plantilla
  usa `[tool.hatch.build.targets.wheel] packages = ["src/{{PACKAGE_NAME}}"]`
  para que el proyecto generado sí sea instalable. La distinción de los
  tres nombres queda registrada en `docs/architecture.md`, en
  `template/docs/architecture.md`, en `docs/glossary.md`, en
  `template/docs/glossary.md` y en el `README.md` raíz. El defecto original
  (nombre visible usado como distribución) está documentado en
  `docs/mistakes.md` con su corrección y su prevención.
- **Reversibilidad**: difícil. Cambiar la separación de los tres nombres
  requiere reescribir `tools/new_project.py`, los tests asociados y toda la
  documentación que los describe. Migrar a otra estrategia de generación
  (Copier, repositorio de ejemplo) implica reescribir `tools/` y los docs.

## ADR-009: el destino debe ser inexistente y la generación usa staging temporal

- **Fecha**: 2026-07-23
- **Estado**: aceptada.
- **Contexto**: generar un proyecto sobre un destino existente es destructivo. Una generación parcial (por error, corte de energía, conflicto de filesystem) podría dejar archivos a medio escribir o mezclados con contenido previo del usuario.
- **Decisión**: el destino final **no debe existir** al iniciar la generación. Si existe, aunque esté vacío, el generador lo rechaza con código de salida distinto de cero. La generación se realiza primero en un directorio de staging temporal dentro del **mismo directorio padre** del destino, usando `tempfile.mkdtemp(prefix=".new_project_", dir=parent)`. Solo tras pasar las validaciones (placeholders resueltos, sin secretos, sin artefactos prohibidos, paths obligatorios presentes) el staging se mueve al destino final con `Path.rename`. Si ocurre cualquier error, el staging se elimina y el destino final no se crea. Los argumentos se validan **antes** de crear el staging o cualquier archivo.
- **Alternativas consideradas**:
  - Generar directamente sobre el destino con `exist_ok=True` o fusión: descartado por riesgo de sobrescritura y mezcla.
  - Crear el staging en `/tmp` y luego mover al destino: descartado por posibles movimientos entre filesystems y por ensuciar `/tmp` con generaciones fallidas.
  - Validar argumentos, crear staging, generar, validar y mover en pasos separados: adoptado. Permite limpiar el staging de forma atómica ante errores parciales.
- **Consecuencias**: el generador es atómico desde el punto de vista del usuario: o aparece el proyecto completo, o no aparece nada. La misma generación ejecutada dos veces sobre el mismo destino falla la segunda vez, porque el destino ya existe. Esto es la propiedad que el usuario espera; no se persigue "idempotencia" en el sentido de re-ejecución silenciosa.
- **Reversibilidad**: fácil. Cambiar la política (por ejemplo, permitir destino vacío preexistente) requeriría modificar el check inicial en `tools/new_project.py` y los tests asociados.
