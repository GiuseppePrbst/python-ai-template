# /verify

Ejecuta los cuatro quality gates obligatorios en orden y reporta el resultado. Detiene y explica cualquier fallo; corrige solo cuando hay una causa identificada.

## Uso

Invocar sin argumentos. El comando se ejecuta desde la raíz del repositorio.

## Pasos

1. Ejecutar en este orden, desde la raíz del repositorio:
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run pyright`
   - `uv run pytest`
2. Capturar el resultado de cada uno.
3. Si todos pasan, declarar el cambio verificado y mostrar un resumen breve.
4. Si alguno falla:
   - Detenerse.
   - Mostrar el comando que falló y la salida relevante.
   - Explicar la causa cuando sea evidente a partir de la salida.
   - **Corregir solo cuando haya una causa identificada.** No relajar reglas, no ampliar ignores, no añadir `noqa` o `type: ignore`, no relajar tipos, no saltarse ni borrar tests para que pase.
   - Volver a ejecutar **todos** los quality gates después de la corrección, no solo el que falló.

## Reglas

- No se considera "verificado" si alguna validación falla.
- No se silencian errores para que el comando termine en verde.
- No se modifican los quality gates sin justificación y sin dejar constancia en `docs/decisions.md`.
- Si la causa del fallo no es evidente tras la primera lectura, se documenta la hipótesis y se detiene la corrección hasta investigar más.

## Salida esperada

- Estado de cada uno de los cuatro gates (pass / fail).
- Veredicto global: **verificado** o **no verificado**.
- Si no está verificado: comando fallido, causa probable y siguiente acción.
