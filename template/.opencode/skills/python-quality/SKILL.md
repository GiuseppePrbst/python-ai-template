# python-quality

Skill para trabajo de calidad en código Python de este repositorio. Carga esta skill cuando vayas a crear, modificar o depurar código Python, o cuando un quality gate falle.

## Cuándo cargar

- Crear o modificar código Python del paquete (`src/{{PACKAGE_NAME}}/`) o de los tests (`tests/`).
- Configurar `ruff`, `pyright` o `pytest`.
- Diagnosticar un fallo de cualquiera de los quality gates.
- Evaluar si una dependencia nueva de runtime o de desarrollo es realmente necesaria.

## Herramientas canónicas

- **Gestor Python**: `uv`. Las dependencias y el entorno virtual se gestionan con `uv sync`, `uv add` y `uv run`.
- **Linter y formateador**: `ruff` (modo `check` + modo `format`).
- **Comprobación de tipos**: `pyright` en modo `strict` (definido en `pyproject.toml`).
- **Tests**: `pytest`, configurado en `pyproject.toml`.

## Reglas de uso

- **No instalar herramientas globalmente.** Todas las herramientas se invocan a través de `uv run` desde la raíz del repositorio.
- **No cambiar la configuración de calidad** (reglas, ignores, niveles, plugins) sin una justificación documentada y, si el cambio es estructural, una entrada en `docs/decisions.md`.
- **No añadir `noqa`, `type: ignore` ni exclusiones de pytest** para que las validaciones pasen. Si una regla molesta, se investiga la causa raíz.
- **No relajar el modo `strict` de pyright.**
- **No añadir dependencias de runtime** por defecto. Toda dependencia nueva requiere justificación y, si es estructural, una ADR.
- Cada cambio debe pasar los cuatro quality gates antes de considerarse terminado.

## Comandos de referencia

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

Para trabajar sobre un archivo o directorio concreto, sustituye el `.` por la ruta.

## Patrones del proyecto

- Layout `src/`: el código del paquete vive en `src/{{PACKAGE_NAME}}/`.
- Versión de Python: 3.12 o superior (`pyproject.toml`).
- Estilo: `ruff` con `line-length = 88`, reglas `E, F, I, UP, B`.
- Tipos: anotaciones explícitas en funciones exportadas y firmas públicas. Pyright en modo `strict` exige tipar también lo interno.
- API pública: lo declarado en `src/{{PACKAGE_NAME}}/__init__.py`. Cambios en la API pública requieren ADR.

## Documentos a consultar

- `AGENTS.md`: reglas obligatorias y quality gates.
- `docs/architecture.md`: estructura y límites del paquete.
- `docs/decisions.md`: decisiones vigentes, en particular ADR-005 (uv) y ADR-007 (quality gates).
- `docs/mistakes.md`: errores recurrentes relacionados con calidad Python.
