/**
 * Plugin de compactación estructurada para `python-ai-template`.
 *
 * Hook utilizado: `experimental.session.compacting` (OpenCode 1.18.4).
 *
 * Contrato (verificado por `/review`):
 *   - El módulo exporta una constante tipada como `Plugin` de
 *     `@opencode-ai/plugin` 1.18.4.
 *   - Registra **únicamente** el hook
 *     `experimental.session.compacting`. No registra ningún otro hook.
 *   - En cada invocación agrega **una sola entrada string** al array
 *     `output.context` del hook. Nunca asigna `output.prompt`.
 *     El prompt por defecto de OpenCode sigue siendo el responsable
 *     del resumen final.
 *   - No usa filesystem. No importa módulos del sistema de archivos.
 *     No lee ni escribe archivos.
 *   - No ejecuta comandos. No usa la interfaz de shell que ofrece
 *     OpenCode.
 *   - No usa la red. No llama a proveedores externos.
 *   - No genera logs permanentes ni escribe en flujos estándar.
 *   - No persiste información. No modifica `docs/decisions.md` ni
 *     ningún archivo del repositorio.
 *   - No intenta reconstruir el estado real del repositorio: deja
 *     esa reconstrucción al propio mecanismo nativo de compactación
 *     de OpenCode y al comando `/handoff`.
 *
 * Naturaleza estática:
 *   La entrada que el plugin añade a `output.context` es una cadena
 *   literal definida como constante en este archivo. No se calcula
 *   en tiempo de ejecución, no se formatea con datos del repositorio
 *   y no se modifica entre invocaciones.
 *
 * Advertencia: el hook `experimental.session.compacting` es
 * **experimental** en OpenCode 1.18.4. Su forma o firma puede cambiar
 * sin aviso. Si deja de funcionar o se renombra, este plugin debe
 * desregistrarse o migrarse a la API vigente mediante una nueva ADR.
 * No se modifica esta implementación en silencio. Si en el futuro
 * deja de ser necesaria, se elimina el archivo y se documenta en una
 * ADR sin reintroducir lógica dinámica.
 *
 * Tipos importados exclusivamente de `@opencode-ai/plugin` 1.18.4
 * (declarado en `.opencode/package.json`). No se añaden dependencias
 * TypeScript nuevas, ni `tsconfig.json`, ni bundler. OpenCode carga
 * el `.ts` directamente con Bun.
 *
 * Ver ADR-012 en `docs/decisions.md`.
 */

import type { Plugin } from "@opencode-ai/plugin"

/**
 * Entrada estática que el plugin añade a `output.context` antes de
 * que el mecanismo nativo de compactación de OpenCode genere el
 * resumen. Es la única fuente de comportamiento del plugin y no se
 * calcula, no se lee ni se transforma en tiempo de ejecución.
 */
const STATIC_COMPACTION_REMINDER = `Recordatorio de compactación estructurada (python-ai-template).

Este bloque es una **instrucción estática** que el plugin \`structured-compaction\` añade a \`output.context\` antes de que el mecanismo nativo de compactación de OpenCode genere el resumen. No es la fuente de verdad del proyecto. La fuente de verdad sigue siendo el código del repositorio, \`docs/current-state.md\` (actualizado por \`/handoff\`), \`docs/decisions.md\` y la documentación versionada.

## Instrucciones para el resumen nativo

OpenCode generará el resumen. Esta instrucción solo **condiciona** ese resumen nativo recordándole las piezas que debe preservar y los límites que debe respetar. El plugin es estático: no lee \`docs/current-state.md\`, no lee \`pyproject.toml\` y no reconstruye el estado real del repositorio; deja esa reconstrucción al propio mecanismo nativo.

### Qué preservar verbatim

Al construir el resumen, conserva exactamente estas diez secciones canónicas del handoff, en este orden, con el contenido que aparezca en \`docs/current-state.md\` al cierre de la sesión o, en su defecto, lo que se haya dicho explícitamente en la conversación:

1. **Objetivo actual**.
2. **Estado de la tarea**.
3. **Hechos verificados**.
4. **Decisiones adoptadas**.
5. **Archivos modificados**.
6. **Validaciones ejecutadas**.
7. **Errores pendientes**.
8. **Enfoques rechazados y motivo**.
9. **Divergencias detectadas**.
10. **Siguiente acción concreta**.

Cuando \`docs/current-state.md\` esté ausente o desactualizado, el resumen debe basarse solo en la conversación y en el código del repositorio. En ese caso, declara explícitamente que esas piezas no se pudieron extraer de un handoff vigente.

### Etiquetado obligatorio dentro del resumen

- Distingue **hechos** de **decisiones**, **hipótesis** y **pendientes**. Las hipótesis no se presentan como conclusiones y los pendientes no se marcan como hechos.
- Conserva los **identificadores ADR** completos (p. ej. \`ADR-007\`, \`ADR-012\`) cuando estén en juego.
- Conserva los **comandos textuales** tal como se invocan en el repositorio (\`uv run python tools/ai/verify.py\`, \`rm -rf dist && uv build && uv run python tools/ai/verify_wheel.py\`, etc.).
- Conserva las **rutas relativas a la raíz** y los **símbolos concretos** (funciones, clases, ADR, archivos) tal como aparecen en el código y en los documentos.

### Divergencias detectadas

Registra sin resolver cualquier incoherencia entre:

- el contenido de \`docs/current-state.md\` y el árbol de trabajo (\`git status --short\`, \`git diff --stat\`);
- el resumen propuesto y un hecho verificable en el código;
- el resumen propuesto y una ADR vigente en \`docs/decisions.md\`.

La resolución de las divergencias **no corresponde** al resumen nativo: corresponde a \`implementer\` o \`documenter\` en una sesión posterior.

### Lo que el resumen debe omitir

- Secretos, claves, tokens, endpoints privados, datos personales, valores reales de variables de entorno.
- Logs completos. Si un log es relevante, cítalo por ruta y rango, no lo copies entero.
- Rutas absolutas del sistema de archivos del usuario.

### Lo que el resumen no debe inventar

- No inventes resultados de validaciones (\`ruff\`, \`pyright\`, \`pytest\`, \`verify_wheel.py\`).
- No inventes entradas de ADR, identificadores simbólicos ni referencias cruzadas que no estén en el código o en los documentos.
- No declares como aprobado un quality gate que no se haya ejecutado explícitamente.

### Carácter auxiliar

El plugin \`structured-compaction\` es un resumen **auxiliar**, no autoridad documental. Si \`docs/current-state.md\` está vigente, el resumen nativo debe contrastarse contra él al cierre de la sesión. Si \`docs/current-state.md\` está ausente, \`/handoff\` debe ejecutarse antes de cerrar el bloque de trabajo.

## Mecanismo de cierre autorizado

El único mecanismo autorizado para mantener \`docs/current-state.md\` al día es \`/handoff\`. Este plugin no lo sustituye; solo condiciona al resumen nativo. Si el bloque de trabajo termina sin \`/handoff\`, la próxima sesión debe empezar por ejecutarlo.`

export const StructuredCompactionPlugin: Plugin = async () => {
  return {
    "experimental.session.compacting": async (_input, output) => {
      output.context.push(STATIC_COMPACTION_REMINDER)
    },
  }
}
