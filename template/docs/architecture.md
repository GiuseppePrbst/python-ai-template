# Arquitectura

Estado vigente de la arquitectura del proyecto y de sus límites. Este documento se mantiene coherente con el código real y con `docs/decisions.md`. Si hay divergencia, prevalece el código y se actualiza este archivo.

## Resumen

`{{PROJECT_NAME}}` es un paquete Python mínimo con layout `src/`, generado a partir de la plantilla `python-ai-template`. Sirve como base portable y verificable de las prácticas descritas en `AGENTS.md` y en `docs/`.

## Tres nombres

En el proyecto ya generado los placeholders están sustituidos y solo se ve
el resultado final. La distinción conceptual sigue siendo relevante porque
define cómo se interpreta cada valor y por qué tres campos pueden coexistir
en `pyproject.toml`, en la documentación y en el código.

- **`{{PROJECT_NAME}}`** — nombre visible del proyecto. Puede contener
  espacios. Aparece en el título de `README.md`, en los docstrings y en los
  textos de la documentación. No se normaliza: se conserva tal cual el
  usuario lo entregó al generar el proyecto.
- **`{{PACKAGE_NAME}}`** — nombre importable del paquete Python. Aparece en
  `src/{{PACKAGE_NAME}}/`, en los imports y en
  `[tool.hatch.build.targets.wheel] packages`. Es el único nombre que se usa
  en código Python.
- **`{{DISTRIBUTION_NAME}}`** — nombre técnico de distribución, derivado de
  `{{PACKAGE_NAME}}` mediante `package_name.lower().replace("_", "-")`.
  Aparece exclusivamente en `[project].name` de `pyproject.toml`. Cumple
  el patrón PEP 503/508 `^[a-z0-9]+(?:-[a-z0-9]+)*$`. No es visible en
  código Python: solo en metadatos del proyecto.

## Componentes

- `src/{{PACKAGE_NAME}}/`: código fuente del paquete.
  - `__init__.py`: punto de entrada público del paquete. Declara `__all__`.
- `tests/`: tests unitarios con `pytest`. Cada test reside en `tests/test_<modulo>.py`.
- `pyproject.toml`: configuración de `uv`, `ruff`, `pyright` y `pytest`.
- `uv.lock`: lockfile reproducible gestionado por `uv`.
- `README.md`: descripción del proyecto y guía rápida de uso.
- `AGENTS.md`: reglas operativas para cualquier agente (humano o IA).
- `docs/`: documentación estructurada (arquitectura, decisiones, errores, glosario, pendientes, estado actual, IA).
- `.opencode/`: configuración de OpenCode específica del proyecto.
  - `agents/`: definiciones de agentes (`implementer`, `reviewer`, `debugger`, `documenter`).
  - `commands/`: comandos slash (`/verify`, `/handoff`, `/decision`, `/mistake`).
  - `skills/`: skills (`python-quality`, `architecture-review`).
- `opencode.jsonc`: configuración de OpenCode del proyecto. Hereda modelo, provider y API key de la configuración global.

## Límites vigentes

- El proyecto es una librería Python, no un servicio. No expone endpoints, no tiene runtime propio ni ciclo de vida de proceso.
- La API pública está limitada a lo exportado en `src/{{PACKAGE_NAME}}/__init__.py`. Cualquier ampliación requiere una ADR.
- El código de producción vive en `src/`. Los tests viven en `tests/`. No se añade código de producción fuera de `src/`.
- La configuración de herramientas vive en `pyproject.toml` y se ejecuta siempre a través de `uv run`. No se duplica configuración en archivos sueltos.
- La configuración de IA vive en `opencode.jsonc` (proyecto) y en `~/.config/opencode/opencode.json` (global). El modelo, provider y API key se definen en el global; el proyecto nunca debe duplicar secretos.
- Los archivos `AGENTS.md`, `docs/` y `.opencode/` definen la operativa de los agentes. Cualquier cambio en esos archivos se trata como cambio de arquitectura.

## Dependencias

- **Runtime**: ninguna declarada en `pyproject.toml` por diseño. La librería no debe añadir dependencias de runtime sin una ADR.
- **Desarrollo**: `pyright`, `pytest`, `ruff`. Gestionadas con `uv` como dev-dependencies.

## Fuera de alcance

- Servicios web, bases de datos, colas o cualquier infraestructura remota.
- Frameworks de UI o plantillas web.
- Dependencias de runtime añadidas por defecto.
- Múltiples paquetes Python dentro del mismo repositorio.
- Integraciones con proveedores de IA más allá de los definidos por la configuración global de OpenCode.

## Cambios que requieren aprobación explícita

Cualquier cambio que:

- Añada una dependencia de runtime.
- Modifique la API pública del paquete.
- Introduzca un nuevo módulo o subdivida los existentes.
- Cambie la configuración de calidad (`ruff`, `pyright`, `pytest`).
- Cambie la configuración de OpenCode del proyecto o del global.
- Añada infraestructura remota o servicios externos.
- Modifique los límites entre módulos o con el exterior.
