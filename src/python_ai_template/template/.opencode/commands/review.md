# /review

Lanza el agente `reviewer` sobre el diff vigente del repositorio. Es
un atajo **manual** para invocar la revisión desde el chat. OpenCode
1.18.4 expone `command.execute.before` pero no
`command.execute.after`, así que `/review` **no se automatiza**
mediante hooks.

## Uso

Invocar sin argumentos. Si se pasa un argumento, se interpreta como
filtro o alcance opcional (por ejemplo, una ruta, un agente o un ADR
concreto) y se entrega al `reviewer` para que delimite la revisión.

## Contrato obligatorio

- **Revisar staged, unstaged y untracked.** El material de revisión
  incluye:
  - `git diff` (unstaged).
  - `git diff --staged` (índice).
  - `git diff --cached` (alias del anterior).
  - `git status --short` para localizar archivos untracked.
  - El contenido completo de los archivos untracked, cuando diff no
    baste.
- **Leer archivos completos cuando el diff no sea suficiente.** Si un
  cambio requiere contexto adicional (definiciones, contratos,
  imports, firmas), el revisor abre el archivo entero.
- **Ejecutar gates relevantes** sobre el cambio propuesto:
  `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run pyright`, `uv run pytest`, y, si el cambio toca el
  empaquetado, `uv run python tools/ai/verify_wheel.py` tras
  `rm -rf dist && uv build`. Si un gate no se ejecuta, se declara
  explícitamente en la salida.
- **Revisar arquitectura, compatibilidad, seguridad, tests,
  documentación y alcance** del cambio:
  - **Arquitectura**: ¿rompe límites, dependencias, API pública o
    configuración vigente? ¿Contradice alguna ADR?
  - **Compatibilidad**: ¿rompe consumidores, contratos, formatos,
    interfaces o expectativas de configuración?
  - **Seguridad**: ¿introduce secretos, logs con datos sensibles,
    endpoints privados, nuevas dependencias sin auditoría?
  - **Tests**: ¿hay tests nuevos para los casos relevantes? ¿se han
    saltado o relajado tests existentes?
  - **Documentación**: ¿están actualizados `AGENTS.md`,
    `docs/architecture.md`, `docs/decisions.md`, `docs/glossary.md`,
    `docs/ai/*.md` y los docstrings afectados?
  - **Alcance**: ¿el diff mezcla refactor, formato, lógica y
    documentación sin justificación?
- **No modificar archivos.** Su resultado es un informe; los cambios
  los aplica `implementer` (o el agente que corresponda).
- **No hacer commits.**

## Formato de salida

La salida de `/review` sigue, en este orden, las secciones
obligatorias:

1. **Resumen del cambio** — qué se hizo, en qué archivos y por qué,
   en una o dos frases.
2. **Bloqueantes** — hallazgos que impiden considerar el cambio
   terminado. Cada uno con ruta, línea o símbolo, y recomendación
   concreta.
3. **Mayores** — hallazgos que deberían corregirse antes del
   próximo cambio, con la misma forma.
4. **Menores** — mejoras opcionales no bloqueantes.
5. **Observaciones** — notas informativas sin acción requerida.
6. **Validaciones ejecutadas** — gates corridos y resultado
   (pass / fail / no ejecutado). Indicar **explícitamente** qué
   validaciones no se corrieron.
7. **Cambios fuera de alcance** — diffs que aparecen en la
   revisión pero no pertenecen al cambio declarado.
8. **Veredicto final** — uno de los cuatro valores permitidos.

## Veredictos permitidos

- **Aprobado** — el cambio cumple todos los criterios.
- **Aprobado con cambios menores** — el cambio se acepta con la
  condición de aplicar los hallazgos menores antes del próximo
  cambio.
- **Requiere cambios** — el cambio tiene hallazgos mayores o
  bloqueantes que deben corregirse antes de aprobarse.
- **Rechazado** — el cambio tiene bloqueantes que invalidan el
  trabajo actual (contradicción con ADR, secretos, tests rotos,
  etc.).

## Reglas adicionales

- Si el diff incluye cambios en `docs/decisions.md`, comprobar que se
  ha añadido una entrada nueva y que **no** se ha reescrito una ADR
  anterior en silencio.
- Si el diff incluye cambios en `opencode.jsonc` o en
  `.opencode/`, comprobar que la documentación de contexto y
  `docs/architecture.md` siguen siendo coherentes con el cambio.
- Si el diff incluye nuevos plugins en `.opencode/plugins/`,
  comprobar que el plugin declara su contrato (qué hook registra,
  qué mutaciones hace, qué no hace) y, en particular, que cumple
  el contrato de los plugins de compactación cuando aplique:

  - **No escribe archivos.**
  - **No lee archivos mediante filesystem** (sin importar
    `node:fs`, `node:fs/promises`, `node:path` ni equivalente;
    sin llamar a `readFile`, `writeFile`, `readdir`, `stat`,
    `resolve`, `join` ni equivalente).
  - **No usa shell** (sin `BunShell` (`$`) ni equivalente).
  - **No llama a la red.**
  - **No genera logs permanentes.**
  - **No modifica `output.prompt`.**
  - **Sólo agrega contexto auxiliar a `output.context`** (una o
    varias entradas, cada una como cadena literal definida en el
    propio plugin).
- Si el diff introduce dependencias de runtime, **rechazar**.
- Si un quality gate falla, el veredicto **no puede** ser
  "Aprobado" ni "Aprobado con cambios menores".

## Salida esperada

- Las ocho secciones del formato de salida, en orden.
- Veredicto inequívoco entre los cuatro permitidos.
- Propuestas (no acciones) de entradas en `docs/mistakes.md` o
  `docs/decisions.md` si la revisión las detecta.
