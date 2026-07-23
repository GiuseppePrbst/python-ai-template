# /verify

Ejecuta el orquestador canónico de los quality gates y, cuando aplique, la
validación del empaquetado. Detiene y explica cualquier fallo; corrige solo
cuando hay una causa identificada.

## Uso

Invocar sin argumentos. El comando se ejecuta desde la raíz del repositorio.

## Pasos

1. Ejecutar primero el orquestador canónico desde la raíz del repositorio:

   ```bash
   uv run python tools/ai/verify.py
   ```

   Detrás de este comando se ejecutan, en este orden, los cuatro gates
   obligatorios:

   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run pyright`
   - `uv run pytest`

   El script se detiene al primer fallo y propaga su `exit code`.

2. Cuando el cambio afecte al empaquetado (wheel, sdist, plantilla o
   `pyproject.toml`), ejecutar además, desde la raíz del repositorio:

   ```bash
   rm -rf dist
   uv build
   uv run python tools/ai/verify_wheel.py
   ```

   `verify_wheel.py` confirma que `pyproject.toml`, `__version__`, el
   nombre del wheel y `METADATA Version` coinciden, y que el wheel
   contiene los cinco recursos obligatorios de la plantilla.

3. Capturar el resultado de cada paso.
4. Si todos pasan, declarar el cambio verificado y mostrar un resumen breve.
5. Si alguno falla:
   - Detenerse.
   - Mostrar el comando que falló y la salida relevante.
   - Explicar la causa cuando sea evidente a partir de la salida.
   - **Corregir solo cuando haya una causa identificada.** No relajar reglas, no ampliar ignores, no añadir `noqa` o `type: ignore`, no relajar tipos, no saltarse ni borrar tests para que pase.
   - Volver a ejecutar **todos** los pasos desde el principio después de la corrección, no solo el que falló.

## Reglas

- No se considera "verificado" si alguna validación falla.
- No se silencian errores para que el comando termine en verde.
- No se modifican los quality gates sin justificación y sin dejar constancia en `docs/decisions.md`.
- Si la causa del fallo no es evidente tras la primera lectura, se documenta la hipótesis y se detiene la corrección hasta investigar más.

## Salida esperada

- Estado de cada paso (pass / fail).
- Veredicto global: **verificado** o **no verificado**.
- Si no está verificado: comando fallido, causa probable y siguiente acción.
