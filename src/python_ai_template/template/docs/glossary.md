# Glosario

Términos usados en el repositorio y en su documentación. Si un término aparece en este glosario, debe usarse con el mismo significado en el resto de documentos.

## Términos del proyecto

- **{{PROJECT_NAME}}**: nombre visible del proyecto. Puede contener espacios.
  Se usa en `README.md`, en los docstrings visibles y en los textos de la
  documentación. No se normaliza.
- **{{PACKAGE_NAME}}**: nombre importable del paquete Python. Debe ser
  `str.isidentifier()`, no keyword de Python y solo ASCII. Se usa en
  `src/{{PACKAGE_NAME}}/`, en los imports y en la configuración de
  paquetes (`[tool.hatch.build.targets.wheel] packages`).
- **{{DISTRIBUTION_NAME}}**: nombre técnico de distribución derivado de
  `{{PACKAGE_NAME}}` mediante la regla
  `package_name.lower().replace("_", "-")`. Se valida con la expresión
  regular `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Se usa exclusivamente en
  `[project].name` de `pyproject.toml`. No es un argumento CLI: se deriva
  siempre del paquete.
- **OpenCode**: herramienta de agente cotidiano. Configuración global en `~/.config/opencode/opencode.json`, configuración de proyecto en `opencode.jsonc`. Ver ADR-002.
- **Modelo diario**: modelo de lenguaje usado por defecto para el trabajo cotidiano. Configurado en la configuración global. Ver `docs/ai/model-policy.md`.
- **Vía de escalamiento premium**: modelo al que se recurre cuando el modelo diario no alcanza tras ciclos razonables. Ver `docs/ai/model-policy.md`.
- **uv**: gestor Python canónico. Ver ADR-005.
- **Quality gates**: conjunto de validaciones automáticas obligatorias (`ruff check`, `ruff format --check`, `pyright`, `pytest`). Ver `AGENTS.md` y ADR-007.
- **Plantilla mantenible**: objetivo de la base: servir como punto de partida portable entre distintos agentes y herramientas.

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
