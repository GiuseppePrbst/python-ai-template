# Glosario

Términos usados en el repositorio y en su documentación. Si un término aparece en este glosario, debe usarse con el mismo significado en el resto de documentos.

## Términos del proyecto

- **python-ai-template**: nombre de este repositorio, del paquete distribuible
  y de la plantilla generadora. Es un paquete Python instalable que produce
  proyectos nuevos a partir de la plantilla empaquetada como `package data`.
  Ver ADR-008 y ADR-010.
- **python_ai_template**: nombre importable del paquete. Vive en
  `src/python_ai_template/`. Es la distribucion Python de `python-ai-template`.
- **Plantilla generadora**: repositorio cuyo propósito es producir proyectos
  nuevos ejecutando un generador sobre un árbol de archivos parametrizado.
  Ver ADR-008.
- **Generador**: modulo `python_ai_template.generator` que produce un proyecto
  a partir de la plantilla. Solo usa la biblioteca estandar. La funcion
  publica es `generate(project_name, package_name, destination)`.
- **Console script**: ejecutable registrado en `pyproject.toml` bajo
  `[project.scripts]`. En este proyecto,
  `new-python-project = "python_ai_template.cli:main"` se instala con
  `uv tool install .` y queda disponible en `PATH` desde cualquier
  directorio. Ver ADR-010.
- **CLI**: modulo `python_ai_template.cli`. Define el `ArgumentParser` y la
  funcion `main(argv)`. Es la entrada canonica para el console script y
  para el shim local.
- **Shim local**: `tools/new_project.py`. Añade `<repo>/src` al principio
  de `sys.path`, importa `python_ai_template.cli.main` y termina con
  `raise SystemExit(main())`. Representa el checkout local y se usa
  durante el desarrollo sin instalar. No intenta caer a una version
  instalada del paquete. Ver ADR-010.
- **src layout**: organizacion del codigo en `src/<paquete>/`. Hatchling
  lo usa como raiz del paquete; todos los archivos bajo
  `src/python_ai_template/`, incluidos los ocultos, se incluyen en el
  wheel. Ver ADR-010.
- **package data**: archivos no Python que se distribuyen dentro del
  paquete. En este proyecto, `src/python_ai_template/template/` se
  distribuye como `package data` y se accede en runtime con
  `importlib.resources.files("python_ai_template").joinpath("template")`.
- **importlib.resources**: API de la biblioteca estandar para acceder a
  recursos de un paquete. Devuelve un `Traversable` que se puede recorrer
  sin materializar el contenido a disco. Ver ADR-010.
- **Traversable**: interfaz de `importlib.resources.abc` (anteriormente
  `importlib.abc`) que representa un archivo o directorio dentro de un
  paquete. Expone `iterdir()`, `is_dir()`, `is_file()`, `read_text()` y
  `__truediv__`. El generador lo recorre recursivamente con la funcion
  `_walk_template`.
- **Staging**: directorio temporal donde el generador escribe el árbol
  antes de moverlo al destino final. Ver ADR-009.
- **Proyecto generado**: proyecto nuevo producido por una invocacion
  exitosa del generador. Contiene su propio `pyproject.toml`, su propio
  `AGENTS.md`, su propia configuración de OpenCode y su propio historial
  de cambios.
- **OpenCode**: herramienta de agente cotidiano. Configuracion global en
  `~/.config/opencode/opencode.json`, configuracion de proyecto en
  `opencode.jsonc`. Ver ADR-002.
- **Modelo diario**: modelo de lenguaje usado por defecto para el trabajo
  cotidiano. Configurado en la configuracion global. Ver
  `docs/ai/model-policy.md`.
- **Via de escalamiento premium**: modelo al que se recurre cuando el
  modelo diario no alcanza tras ciclos razonables. Ver
  `docs/ai/model-policy.md` y ADR-004.
- **uv**: gestor Python canonico. Ver ADR-005.
- **Quality gates**: conjunto de validaciones automaticas obligatorias
  (`ruff check`, `ruff format --check`, `pyright`, `pytest`). Ver
  `AGENTS.md` y ADR-007.
- **Bootstrap**: bloque inicial de configuracion y documentacion que deja
  un proyecto listo para operar.

## Términos operativos

- **Sesion**: bloque de trabajo continuo con un agente. Se cierra
  idealmente con `/handoff`.
- **Handoff**: traspaso del estado de trabajo al final de una sesion, via
  comando `/handoff` y `docs/current-state.md`.
- **ADR**: Architecture Decision Record. Entrada en `docs/decisions.md`
  con formato ligero (ID, fecha, contexto, decision, alternativas,
  consecuencias, reversibilidad, estado).
- **Workaround**: solucion provisional. Solo se introduce tras identificar
  la causa raiz y dejar constancia de por que es necesaria. Ver
  `AGENTS.md`.
- **Definicion de terminado**: lista de condiciones en `AGENTS.md` que un
  cambio debe cumplir para darse por cerrado.

## Términos de IA

- **Contexto minimo**: practica de cargar solo la documentacion necesaria
  para la tarea en curso, no `docs/` completo. Ver
  `docs/ai/context-policy.md`.
- **Compactacion**: reduccion automatica del contexto de conversacion
  cuando se acerca al limite. Configurada en `opencode.jsonc`.
- **Reserva de contexto** (`reserved`): tokens que OpenCode mantiene
  libres para evitar quedarse sin espacio durante operaciones largas.
  Valor vigente: 16000.
- **Escalamiento**: paso del modelo diario al modelo premium tras ciclos
  fallidos. Ver `docs/ai/model-policy.md`.
- **Evaluacion**: registro de un experimento concreto con un modelo en
  una tarea real. Ver `docs/ai/evaluations.md`.
