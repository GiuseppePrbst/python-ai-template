# /decision

Registra una nueva entrada en `docs/decisions.md` siguiendo el formato ADR ligero del proyecto.

## Uso

`/decision <id-corto> <titulo-corto>`

Ejemplo: `/decision adr-008 usar-httpx-en-lugar-de-requests`.

El ID debe ser correlativo con los existentes (último ADR conocido + 1). El título se usa solo como referencia; el documento final lleva todos los campos normalizados.

## Pasos

1. Recopilar del contexto:
   - **Contexto**: qué situación o problema motiva la decisión.
   - **Decisión**: qué se ha decidido.
   - **Alternativas consideradas** y por qué se descartaron.
   - **Consecuencias**: efectos esperados, tanto positivos como negativos.
   - **Reversibilidad**: si la decisión es fácil, difícil o imposible de revertir.
   - **Estado**: `propuesta`, `aceptada`, `rechazada` o `superseded by ADR-XXX`.
2. Asignar un ID correlativo siguiendo la numeración existente.
3. Añadir la entrada a `docs/decisions.md` respetando el formato de las anteriores (mismo orden de campos, mismo nivel de detalle).
4. Fijar la fecha al alta (formato `YYYY-MM-DD`).
5. Si la decisión invalida una anterior, añadir la referencia cruzada y marcar la anterior como `Superseded by ADR-XXX`.

## Reglas

- **No modificar decisiones históricas silenciosamente.** Cualquier corrección se hace añadiendo una nueva entrada que las referencia y corrige.
- **No incluir secretos**, claves, tokens ni datos sensibles.
- No hacer commits.
- No decidir sin contexto suficiente: si falta información, se documenta la hipótesis y se marca como `propuesta`.

## Salida esperada

- Entrada nueva en `docs/decisions.md` con todos los campos: ID, fecha, contexto, decisión, alternativas, consecuencias, reversibilidad, estado.
- Si reemplaza una decisión previa, referencia cruzada en ambas entradas.
