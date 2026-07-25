# Evaluación de compactación estructurada — v0.3.3

## Alcance

Este documento evalúa una sesión de OpenCode 1.18.4 con el plugin
`structured-compaction` habilitado, instalada desde el origen local
de la plantilla. La prueba buscaba verificar si, ante una compactación
nativa del SDK, el resumen post-compactación preservaba el contenido
del checkpoint sintético distribuido. El alcance de la evaluación
**no** permite aislar el efecto causal del plugin: el plugin no
produce logs ni telemetría, por lo que cualquier diferencia entre
una sesión con plugin y una sesión sin plugin no es directamente
atribuible a él.

> “La influencia causal del plugin no es observable directamente porque el
> plugin no produce logs ni telemetría.”

## Metodología

- **Versión de OpenCode**: `1.18.4`.
- **Fixtures distribuidos**: checkpoint sintético con diez headings
  canónicos y once marcadores literales, y filler neutro
  metalingüístico, cargados literalmente en la sesión.
- **Presupuesto**: máximo tres ciclos de carga y veinte minutos
  totales por corrida.
- **Evidencia exigida**: atribuible a la misma sesión evaluada; las
  inferencias sin evento en log no cuentan.
- **Comandos**: solo los documentados y verificables; queda
  prohibido inventar comandos para forzar compactación.
- **Sin medición de tokens** en ningún momento de la corrida.
- **Logs completos**: almacenados fuera del repositorio y citados
  solo como extracto resumido, nunca copiados íntegros.
- **Clasificación independiente**: cada modelo se evalúa por
  separado; la no disponibilidad de uno no convierte al otro
  en `inconclusive`.

## Corrida MiniMax

- **Modelo**: `MiniMax-M3`.
- **Proveedor**: `minimax-direct`.
- **Variante**: `default`.
- **Compaction**:
  - `auto: true`.
  - `prune: true`.
  - `reserved: 16000`.
- **Plugin habilitado**: sí.
- **Compactación nativa confirmada**: no.
- **Evidencia relacionada con la misma sesión**: sí.
- **Resumen post-compactación**: inexistente.
- **Headings recuperados**: no evaluable.
- **Marcadores literales recuperados**: no evaluable.
- **Contenido semántico recuperado**: no evaluable.
- **Marcadores perdidos**: no determinable.
- **Hechos inventados**: no evaluable.
- **`NEXT-01`**: no evaluable.
- **Corrección humana**: repetir la prueba solo ante un mecanismo
  observable o una configuración materialmente distinta.
- **Cambios adicionales atribuibles a la corrida**: no.
- **Duración medida**: 11,05 minutos.
- **Resultado**: `inconclusive`.
- **Limitación principal**: presupuesto agotado sin compactación
  confirmada.

## Corrida Codex

- **OpenCode**: `1.18.4`.
- **Modelo**: `gpt-5.6-sol`.
- **Proveedor**: `openai`.
- **Variante**: `medium`.
- **Compaction**:
  - `auto: true`.
  - `prune: true`.
  - `reserved: 16000`.
- **Plugin habilitado**: sí.
- **Compactación nativa confirmada**: no.
- **Evidencia relacionada con la misma sesión**: sí.
- **Resumen post-compactación**: inexistente.
- **Headings recuperados**: no evaluable.
- **Marcadores literales recuperados**: no evaluable.
- **Contenido semántico recuperado**: no evaluable.
- **Marcadores perdidos**: no determinable.
- **Hechos inventados**: no evaluable.
- **`NEXT-01`**: no evaluable.
- **Corrección humana**: no aplicable porque no hubo resumen.
- **Cambios adicionales atribuibles a la corrida**: no.
- **Duración medida**: 2,47 minutos.
- **Resultado**: `inconclusive`.
- **Limitación principal**: tres ciclos agotados sin compactación
  confirmada.

## Comparación

| Criterio | MiniMax | Codex |
|---|---|---|
| Compactación confirmada | no | no |
| Resumen disponible | no | no |
| Headings | no evaluable | no evaluable |
| Marcadores literales | no evaluable | no evaluable |
| Contenido semántico | no evaluable | no evaluable |
| `NEXT-01` | no evaluable | no evaluable |
| Cambios atribuibles en Git | no | no |
| Duración | 11,05 minutos | 2,47 minutos |
| Resultado | `inconclusive` | `inconclusive` |

## Incidente operativo

Durante la inspección de configuración de OpenCode, una salida
expuso una credencial del proveedor. El valor **no** se conserva en
este documento ni en ningún artefacto del repositorio. La credencial
afectada debe revocarse o rotarse. Las futuras inspecciones de
configuración deben sanitizar la salida antes de citarla o
almacenarla.

## Conclusión final

Ambas corridas — MiniMax y Codex — fueron `inconclusive`. Ninguna
produjo una compactación nativa confirmada y, en consecuencia, no
existió un resumen post-compactación que permitiera evaluar la
retención de headings, marcadores, decisiones o siguiente acción. No
se observaron cambios en Git atribuibles a las corridas. Por tanto,
**no existe evidencia para aprobar, rechazar ni simplificar el plugin
sobre la base de su comportamiento real**: el plugin permanece en
estado experimental. No se repetirán corridas idénticas sin un
mecanismo observable o una configuración materialmente distinta.

> “La influencia causal del plugin no es observable directamente porque el
> plugin no produce logs ni telemetría.”

## Limitaciones

- La compactación no fue observable en ninguna corrida.
- El árbol Git tenía cambios preexistentes antes de la corrida
  MiniMax; no aparecieron cambios adicionales durante ninguna de las
  dos corridas.
- La causalidad del plugin no es observable.
- Una credencial se expuso durante la inspección de configuración.
- Ambas corridas agotaron el presupuesto sin compactación confirmada.
