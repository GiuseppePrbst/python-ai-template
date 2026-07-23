# Glosario

Términos usados en el repositorio y en su documentación. Si un término aparece en este glosario, debe usarse con el mismo significado en el resto de documentos.

## Términos del proyecto

- **python-ai-template**: nombre de este repositorio y de la plantilla generadora. No es un paquete Python instalable: es una herramienta que produce paquetes instalables a partir de `template/`.
- **Plantilla generadora**: repositorio cuyo propósito es producir proyectos nuevos ejecutando un generador sobre un árbol de archivos parametrizado. Ver ADR-008.
- **Generador**: script ejecutable que produce un proyecto a partir de la plantilla. En este repositorio vive en `tools/new_project.py`. Solo usa la biblioteca estándar.
- **Staging**: directorio temporal donde el generador escribe el árbol antes de moverlo al destino final. Ver ADR-009.
- **Proyecto generado**: proyecto nuevo producido por una invocación exitosa del generador. Contiene su propio `pyproject.toml`, su propio `AGENTS.md`, su propia configuración de OpenCode y su propio historial de cambios.
- **OpenCode**: herramienta de agente cotidiano. Configuración global en `~/.config/opencode/opencode.json`, configuración de proyecto en `opencode.jsonc`. Ver ADR-002.
- **Modelo diario**: modelo de lenguaje usado por defecto para el trabajo cotidiano. Configurado en la configuración global. Ver `docs/ai/model-policy.md`.
- **Vía de escalamiento premium**: modelo al que se recurre cuando el modelo diario no alcanza tras ciclos razonables. Ver `docs/ai/model-policy.md` y ADR-004.
- **uv**: gestor Python canónico. Ver ADR-005.
- **Quality gates**: conjunto de validaciones automáticas obligatorias (`ruff check`, `ruff format --check`, `pyright`, `pytest`). Ver `AGENTS.md` y ADR-007.
- **Bootstrap**: bloque inicial de configuración y documentación que deja un proyecto listo para operar.

## Términos operativos

- **Sesión**: bloque de trabajo continuo con un agente. Se cierra idealmente con `/handoff`.
- **Handoff**: traspaso del estado de trabajo al final de una sesión, vía comando `/handoff` y `docs/current-state.md`.
- **ADR**: Architecture Decision Record. Entrada en `docs/decisions.md` con formato ligero (ID, fecha, contexto, decisión, alternativas, consecuencias, reversibilidad, estado).
- **Workaround**: solución provisional. Solo se introduce tras identificar la causa raíz y dejar constancia de por qué es necesaria. Ver `AGENTS.md`.
- **Definición de terminado**: lista de condiciones en `AGENTS.md` que un cambio debe cumplir para darse por cerrado.

## Términos de IA

- **Contexto mínimo**: práctica de cargar solo la documentación necesaria para la tarea en curso, no `docs/` completo. Ver `docs/ai/context-policy.md`.
- **Compacción**: reducción automática del contexto de conversación cuando se acerca al límite. Configurada en `opencode.jsonc`.
- **Reserva de contexto** (`reserved`): tokens que OpenCode mantiene libres para evitar quedarse sin espacio durante operaciones largas. Valor vigente: 16000.
- **Escalamiento**: paso del modelo diario al modelo premium tras ciclos fallidos. Ver `docs/ai/model-policy.md`.
- **Evaluación**: registro de un experimento concreto con un modelo en una tarea real. Ver `docs/ai/evaluations.md`.
