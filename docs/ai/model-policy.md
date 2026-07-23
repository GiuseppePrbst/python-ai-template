# Política de modelos

Cómo se eligen los modelos de lenguaje para cada tarea. Esta política se aplica en combinación con `AGENTS.md`, con las ADR-003 y ADR-004 y con `docs/ai/evaluations.md`.

## Modelo diario

- **MiniMax M3** (`minimax-direct/MiniMax-M3`) es el modelo de uso cotidiano.
- Está pensado para: tareas mecánicas, implementación guiada, refactor pequeño, formato, tests rutinarios, documentación operativa y validaciones.
- Está configurado en `~/.config/opencode/opencode.json`. El proyecto no duplica modelo, provider ni API key.

## Modelo premium

- **ChatGPT Codex** es la vía de escalamiento premium.
- Reservar para: arquitectura, migraciones amplias, debugging complejo, seguridad, refactors difíciles de revertir y tareas donde el costo de un error es alto.
- No usar en tareas mecánicas o repetitivas, aunque la respuesta "parezca mejor".

## Reglas de escalamiento

- Escalar a Codex **después de dos ciclos razonables fallidos con MiniMax**. Un ciclo se considera razonable cuando:
  1. La hipótesis sobre la causa del problema está formulada explícitamente.
  2. Se ha buscado evidencia en código, configuración y logs.
  3. Se han aplicado los quality gates sobre el cambio intentado.
- Anotar cada escalamiento en `docs/ai/evaluations.md` con motivo, resultado y correcciones humanas necesarias.
- Si el escalamiento a Codex tampoco resuelve el problema, replantear la hipótesis antes de iniciar un nuevo ciclo. Más modelo no sustituye a una mejor pregunta.

## Lo que no se hace

- No se usan modelos premium en tareas mecánicas.
- No se cambia de modelo en mitad de un mismo ciclo sin documentar el motivo.
- No se compara el rendimiento "en abstracto": se compara tarea a tarea, con evidencia concreta en `docs/ai/evaluations.md`.
- No se introducen nuevos modelos o proveedores sin una ADR.

## Documentos relacionados

- `docs/ai/evaluations.md`: registro de evaluaciones concretas.
- `docs/ai/context-policy.md`: gestión del contexto al usar cada modelo.
- `docs/decisions.md`: ADR-003 (MiniMax M3) y ADR-004 (Codex).
- `AGENTS.md`: reglas generales y definición de terminado.
