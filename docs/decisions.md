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

## ADR-010: el repositorio pasa a ser un paquete instalable con src layout

- **Fecha**: 2026-07-23
- **Estado**: aceptada.
- **Contexto**: hasta la fase 3, el repositorio era un proyecto plano con `tools/new_project.py` como generador y `template/` como directorio hermano. `pyproject.toml` declaraba `[tool.uv] package = false` y el generador localizaba la plantilla mediante `Path(__file__).resolve().parent.parent / "template"`. Esto hacia imposible distribuir el generador: ni `uv tool install .` ni `pip install .` producían nada instalable, y el console script `new-python-project` que el usuario necesitaba para crear proyectos desde cualquier directorio no existía. Cualquier intento de reutilizar la herramienta exigia clonar el repositorio o copiar `tools/new_project.py` y `template/` a mano, con el riesgo de divergencia asociado.
- **Decisión**: el repositorio adopta **src layout** y se distribuye como paquete `python-ai-template` (importable como `python_ai_template`). Cambios concretos:
  - **src layout**: el código del paquete vive en `src/python_ai_template/`. Hatchling (`[tool.hatch.build.targets.wheel] packages = ["src/python_ai_template"]`) incluye todo el árbol del paquete, incluidos los archivos ocultos como `.gitignore` y `.opencode/.gitignore`. Verificación: `unzip -l dist/python_ai_template-0.1.0-py3-none-any.whl` lista los archivos obligatorios.
  - **template como package data**: `template/` se mueve dentro del paquete, a `src/python_ai_template/template/`. Asi viaja con el wheel y no depende de la ruta del repositorio.
  - **importlib.resources**: la generacion accede a la plantilla con `importlib.resources.files("python_ai_template").joinpath("template")`, que devuelve un `Traversable`. Una funcion pequena y tipada, `_walk_template`, lo recorre recursivamente en orden determinista, conservando literalmente nombres como `.gitignore`, `.opencode`, `__package_name__` y archivos `.tmpl`. El resto del pipeline (render, validacion, staging, rename) opera sobre el `Path` real del staging, exactamente igual que en la version previa.
  - **Console script**: `pyproject.toml` declara `[project.scripts] new-python-project = "python_ai_template.cli:main"`. `uv tool install .` deja el ejecutable disponible en `PATH` desde cualquier directorio.
  - **CLI con `--version` y `--help`**: `cli.py` usa `argparse` con `action="version"` (sin clases `Action` personalizadas) que imprime `__version__` desde `python_ai_template.__init__`.
  - **Shim local**: `tools/new_project.py` se conserva como shim determinista: añade `<repo>/src` al principio de `sys.path`, importa `python_ai_template.cli.main` y termina con `raise SystemExit(main())`. No intenta caer a una version instalada del paquete. Representa el checkout local; el console script representa la version instalada.
  - **de `package = false` a paquete construible**: se elimina `[tool.uv] package = false`. `[tool.pyright]` y `[tool.pytest.ini_options]` apuntan a `src/` para localizar el paquete. Se conservan `ruff`, `pyright` y `pytest` como dev-deps.
  - **Sin dependencias de runtime**: solo biblioteca estandar (`argparse`, `keyword`, `re`, `shutil`, `sys`, `tempfile`, `importlib.resources`, `pathlib`).
- **Alternativas consideradas**:
  - **Mantener el repositorio plano y distribuir solo el generador como script suelto**: descartado porque no permite `uv tool install` ni console script.
  - **Mover `template/` pero seguir leyéndolo desde disco en el código del paquete**: descartado porque mantiene un acoplamiento debil con la ruta de instalacion y exige un paso de copia o enlace posterior a `uv tool install`.
  - **Materializar la plantilla completa en un segundo directorio temporal dentro de `generate()`** (vía `TemporaryDirectory` o `as_file`) y reutilizar la logica basada en `Path`: descartado por la correccion explicita del usuario. Materializar introduce un doble staging (el interno de la plantilla + el staging del proyecto) y obliga a gestionar el ciclo de vida del contexto. Recorrer el `Traversable` directamente y escribir entrada a entrada al staging existente es mas simple y elimina el material.
  - **Usar `py.typed` para marcar el paquete como tipado**: descartado en esta fase porque la API publica (un solo console script) no se ha estabilizado para consumidores externos. Si en el futuro alguien importa `python_ai_template` como libreria, se añadira el marcador en una ADR posterior.
  - **Hacer que el shim intente caer a una version instalada del paquete si la importacion falla**: descartado. El shim representa el checkout local; silenciar fallos de importacion ocultaria inconsistencias entre el codigo en edicion y la version instalada.
  - **Hatchling con `[tool.hatch.build.targets.wheel] only-include = [...]`**: descartado. La inspeccion del wheel confirma que hatchling incluye por defecto todos los archivos bajo `src/python_ai_template/`, incluidos los ocultos, sin necesidad de reglas explicitas.
- **Consecuencias**:
  - El repositorio sigue siendo la fuente de verdad del generador y de la plantilla, pero ahora tambien produce un wheel instalable.
  - `uv tool install .` deja disponible `new-python-project` desde cualquier directorio. `new-python-project --version` imprime `0.1.0`. `new-python-project --help` muestra la ayuda. La validacion E2E exige ejecutarlo desde un directorio externo (p. ej. `/tmp`).
  - `python3 tools/new_project.py ...` sigue funcionando desde la raiz del repositorio para desarrollo rapido sin instalacion.
  - Los 28 tests existentes que importan el modulo por la ruta `tools/` se han migrado a `from python_ai_template import generator as new_project` y se han añadido 5 tests nuevos que validan `cli.main()` directamente: `--version`, `--help`, argumentos de generacion, argumentos faltantes y error de validacion.
  - `docs/architecture.md`, `docs/glossary.md` y `README.md` se actualizan para reflejar la nueva forma de uso y la division entre shim local y console script.
  - El wheel construido se inspecciona con `unzip -l` (o equivalente) y debe listar al menos: `python_ai_template/template/.gitignore`, `python_ai_template/template/.opencode/.gitignore`, `python_ai_template/template/pyproject.toml.tmpl`, `python_ai_template/template/src/__package_name__/__init__.py.tmpl` y `python_ai_template/template/tests/test_smoke.py.tmpl`.
- **Reversibilidad**: media. Revertir requiere: borrar `src/`, restaurar `template/` al nivel raiz, restaurar `tools/new_project.py` con la implementacion anterior, eliminar `[project.scripts]` y restaurar `[tool.uv] package = false` en `pyproject.toml`. La logica de generacion en si misma no cambia, por lo que el historial git permite recuperar la fase 3 sin perdida.

## ADR-011: hardening operativo con scripts locales y CI reproducible

- **Fecha**: 2026-07-23
- **Estado**: aceptada.
- **Contexto**: tras ADR-007 quedó establecida la obligatoriedad de los cuatro quality gates, pero su ejecución era manual y dispersa. `tools/new_project.py` y el paquete se habían vuelto construibles, pero no existía una forma automática y reproducible de (a) encadenar los gates en local con un solo comando que pare en el primer fallo, (b) verificar que el wheel producido contiene todos los recursos de la plantilla y que las cuatro fuentes de la versión están sincronizadas, y (c) ejecutar todo lo anterior en CI sobre cada push y cada pull request, en dos versiones de Python y con build + verificación + artifact únicos. Tampoco existía una política explícita sobre cómo fijar las Actions de GitHub para evitar resurfacing silencioso.
- **Decisión**:
  - **Scripts locales como contrato común local/CI.** Se introducen dos scripts en `tools/ai/`:
    - `verify.py`: orquestador de los cuatro gates canónicos. Solo biblioteca estándar (`subprocess`, `sys`). Ejecuta cada gate con `subprocess.run` pasando una lista de argumentos, sin `shell=True`, sin `capture_output`, con salida en vivo. Imprime un encabezado y el comando de cada gate, se detiene al primer fallo y devuelve exactamente su `exit code` mediante `raise SystemExit(main())`. La CI lo invoca tal cual desde la raíz del repo con `uv run python tools/ai/verify.py`, y es el atajo canónico en local.
    - `verify_wheel.py`: verificador del wheel. Solo biblioteca estándar (`ast`, `pathlib`, `tomllib`, `zipfile`, `sys`). Lee las cuatro fuentes de la versión y exige que coincidan entre sí:
      1. `project.version` de `pyproject.toml` vía `tomllib`.
      2. `__version__` de `src/python_ai_template/__init__.py` mediante extracción estática con `ast`, sin importar ni ejecutar el módulo. Rechaza cero o más de una asignación a `__version__` y exige que el valor sea un string literal.
      3. Nombre del wheel: exige prefijo `python_ai_template-<project.version>-`.
      4. `METADATA Version` dentro del wheel, exigiendo exactamente un `*.dist-info/METADATA`.
      Además exige exactamente un `*.whl` en `dist/` y la presencia de los cinco recursos obligatorios de la plantilla.
  - **Matriz `quality` en Python 3.12 y 3.14.** El job `quality` del workflow `.github/workflows/ci.yml` corre la matriz con `strategy.fail-fast: false`, sobre `ubuntu-latest`, ejecuta `uv sync --locked` y `uv run python tools/ai/verify.py`. `fail-fast: false` se eligió para no perder el diagnóstico de la otra versión cuando una falla.
  - **Build y artifact en job único dependiente.** El job `package` declara `needs: quality`, no usa matriz y fija Python 3.12. Ejecuta `uv sync --locked`, `rm -rf dist`, `uv build`, `uv run python tools/ai/verify_wheel.py` y `actions/upload-artifact`. Como solo corre si **todas** las entradas de la matriz aprueban y el job no se replica por versión, el build y el upload ocurren exactamente una vez por corrida. El artifact se llama `dist`, contiene `dist/*.whl` y `dist/*.tar.gz`, usa `if-no-files-found: error` y `retention-days: 14`.
  - **Actions fijadas por SHA completo.** Las tres Actions (`actions/checkout`, `astral-sh/setup-uv`, `actions/upload-artifact`) van ancladas al SHA completo de 40 caracteres con el tag como comentario:
    - `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`
    - `astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0`
    - `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1`

    El SHA se obtiene del release oficial correspondiente y se fija de manera inmutable; los tags se mantienen como comentario para legibilidad humana. No se publican paquetes ni se crean GitHub Releases desde la pipeline. No se añade `pre-commit` en esta fase.
- **Alternativas consideradas**:
  - **Ejecutar los cuatro gates directamente en CI sin orquestador local**: descartado por divergencia inevitable entre la ejecución local y la remota. El orquestador `verify.py` fija un único contrato que CI y local comparten.
  - **`uv tool install` de un paquete externo con lógica similar**: descartado por añadir dependencia de runtime y por ir contra ADR-005 (`uv` canónico) y el principio de "sin dependencias de runtime" del paquete.
  - **Importar `python_ai_template.__init__` para leer `__version__`**: descartado por ejecutar código del paquete durante la verificación, lo que abre la puerta a errores en el momento de import. Se eligió extracción estática con `ast` sobre el fichero leído como texto.
  - **Reimplementar parsing PEP 427 del nombre del wheel con `packaging` o similar**: descartado por dependencia nueva. La forma del nombre se valida por prefijo y se reconstruye como `parts[1:-3]`, suficiente para el caso actual.
  - **`fail-fast: true` en la matriz**: descartado por perder diagnóstico cuando una versión rompe. Mantener `fail-fast: false` informa de ambas a la vez, con un costo despreciable.
  - **Build y artifact en cada entrada de la matriz**: descartado por duplicación innecesaria y por trabajo desperdiciado en una segunda corrida que ya tiene wheel.
  - **Publicar a PyPI desde la pipeline**: descartado por scope. La pipeline no publica nada ni crea GitHub Releases. La instalación local sigue siendo manual mediante `uv tool install .`.
  - **Anclar Actions por tag móvil (p. ej. `@v7`)** o por SHA abreviado: descartado por riesgo de resurfacing silencioso. Solo se acepta SHA completo de 40 caracteres con el tag como comentario.
  - **Añadir `pre-commit` en esta fase**: pospuesto. No hay evidencia de fricción suficiente y mantiene el cambio acotado. Si en el futuro se justifica, se abordará en una ADR propia.
- **Consecuencias**:
  - El contrato local/CI es único: los cuatro gates se ejecutan con el mismo orquestador, en el mismo orden, con el mismo comportamiento ante fallos.
  - El wheel se valida automáticamente en CI en cuanto a contenido (cinco recursos) y consistencia de versión (cuatro fuentes). Si el día de mañana una de esas fuentes se desincroniza, la CI lo bloquea antes del merge.
  - El artifact `dist` queda disponible por corrida de CI durante 14 días, sin duplicarse por versión de Python.
  - `tools/ai/__pycache__/` queda cubierto por la regla global `__pycache__/` del `.gitignore` raíz; no se añadió una entrada explícita.
  - `pyproject.toml`, `uv.lock`, la lógica del generador, `AGENTS.md`, `docs/` previos y la configuración de OpenCode no se modificaron en esta fase. Tampoco se introdujo ninguna dependencia de runtime nueva.
  - El paquete sigue sin dependencias de runtime. El script `verify_wheel.py` exige el `__init__.py` con una asignación simple a `__version__`; una asignación anotada futura (`__version__: str = "..."`) requeriría una actualización del script (esto queda registrado como tarea de prioridad baja en `docs/todos.md`).
  - La pipeline no es canónica todavía para gobernanza: el job `quality` no aplica las ADR como gate ni bloquea merges sin aprobación humana. Queda como evolución natural, no como regresión.
  - La política de Actions queda documentada en `docs/architecture.md` (sección "Pipeline de validación reproducible (CI/local)") y la badge de CI aparece en `README.md`. La trazabilidad de la decisión queda aquí.
- **Reversibilidad**: fácil. Revertir requiere eliminar `.github/workflows/ci.yml`, eliminar `tools/ai/verify.py` y `tools/ai/verify_wheel.py`, y retirar las menciones en `README.md`, `AGENTS.md`, `.opencode/commands/verify.md` y `docs/architecture.md`. ADR-007 mantendría su vigencia (los cuatro gates siguen siendo obligatorios), pero la ergonomía local/CI perdería el orquestador y la verificación del wheel.
