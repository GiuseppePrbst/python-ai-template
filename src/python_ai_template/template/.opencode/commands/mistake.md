# /mistake

Registra un error recurrente o con valor futuro en `docs/mistakes.md`. No registra errores triviales.

## Uso

`/mistake <titulo-corto>`

Ejemplo: `/mistake pyright-falla-por-version-de-pydantic`.

## Pasos

1. Reproducir el problema y aislar la causa raíz. Sin causa raíz, no se registra.
2. Rellenar la entrada con los campos de la plantilla:
   - **Fecha**: `YYYY-MM-DD`.
   - **Síntoma**: cómo se manifestó el problema (logs, error, comportamiento).
   - **Causa raíz**: por qué ocurrió, con referencia a archivos o comandos si aplica.
   - **Corrección**: qué se cambió para resolverlo.
   - **Prevención**: regla, validación, checklist o automatización que evite que vuelva a ocurrir.
3. Añadir la entrada a `docs/mistakes.md` respetando el formato existente (mismo orden de campos, mismo nivel de detalle).
4. Si la corrección requiere una decisión arquitectónica, proponerla con `/decision`.
5. Si la corrección merece una skill, comando o agente nuevo, proponerlo en el plan correspondiente, no en el registro de errores.

## Reglas

- **No registrar errores triviales** sin valor futuro. Typos de una vez, descuidos puntuales sin patrón y errores que no se repetirán no se documentan.
- **No incluir secretos, datos sensibles ni información personal.**
- **No modificar entradas históricas** salvo para añadir referencias cruzadas.
- No hacer commits.

## Salida esperada

- Entrada nueva en `docs/mistakes.md` con los campos: fecha, síntoma, causa raíz, corrección, prevención.
- Si la corrección implica una decisión arquitectónica, entrada correspondiente en `docs/decisions.md`.
