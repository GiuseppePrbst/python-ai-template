# /compact-test

Prueba manual reproducible y desechable del plugin
`structured-compaction`. No modifica ADR ni `docs/current-state.md`
automaticamente. Diseñada para validar que el plugin sigue siendo
estatico y que la compactacion automatica de OpenCode respeta la
forma canonica del handoff.

## Cuando usarlo

- Tras cualquier cambio al plugin
  `src/python_ai_template/template/.opencode/plugins/structured-compaction.ts`.
- Tras cualquier cambio al formato canonico de
  `docs/current-state.md`.
- Antes de rotar la version mayor del SDK OpenCode.
- Despues de cualquier actualizacion de OpenCode que pueda afectar al
  hook `experimental.session.compacting`.

## Pasos

1. **Crear una sesion nueva.** Inicia una sesion de OpenCode 1.18.4
   sin carga heredada de sesiones previas. Si la version vigente de
   OpenCode expone un mecanismo soportado y verificable para crear
   sesiones limpias (CLI o API), documentalo aqui y usalo. Si no,
   sigue al paso 2 igualmente.

2. **No usar informacion sensible.** El fixture del paso 3 contiene
   solo texto de ejemplo. No incluir secretos, tokens, endpoints
   privados ni datos personales.

3. **Establecer un fixture minimo** pegando el siguiente bloque en la
   conversacion (o cargandolo como contexto inicial). Contiene
   exactamente las piezas que la prueba quiere verificar:

   ```text
   OBJETIVO: verificar que el plugin no rompe las 10 secciones
   canonicas tras una compactacion.

   DECISION: mantener el plugin como entrada estatica.

   ARCHIVO MODIFICADO (ficticio): src/ejemplo.py (no aplica al repo).

   VALIDACION: ruff + pyright + pytest + verify_wheel + verify_opencode.

   ERROR (ficticio): ninguno en el fixture.

   ENFOQUE RECHAZADO: persistir el resumen en disco desde el plugin.

   DIVERGENCIA: ninguna en el fixture.

   SIGUIENTE ACCION: clasificar approved si las 10 secciones siguen
   presentes tras la compactacion.
   ```

4. **Disparar la compactacion disponible en OpenCode 1.18.4.**
   - **Si** OpenCode 1.18.4 expone un comando o API soportada y
     verificable para forzar la compactacion, usala y documenta aqui
     su nombre exacto y su forma de invocacion. En el momento de
     redactar este comando (ADR-013, 2026-07-23) no se ha confirmado
     un mecanismo publico; no se inventa uno.
   - **Si no**, continuar la conversacion hasta que el umbral
     automatico de compactacion se alcance (contexto extenso). Esta
     via es la unica documentada hasta nuevo aviso.

5. **Solicitar el checkpoint recuperado.** Pedir al agente que
   muestre el resumen post-compactacion (o el fragmento disponible
   tras la poda).

6. **Verificar las diez secciones canonicas.** El resumen debe
   permitir reconstruir, total o parcialmente, las diez secciones del
   handoff: objetivo actual, estado de la tarea, hechos verificados,
   decisiones adoptadas, archivos modificados, validaciones
   ejecutadas, errores pendientes, enfoques rechazados y motivo,
   divergencias detectadas, siguiente accion concreta. La forma
   exacta del resumen es responsabilidad del mecanismo nativo de
   OpenCode; este plugin **no** es autoridad documental.

7. **Ejecutar** desde la raiz del repositorio:

   ```bash
   git status --short
   ```

   La salida debe estar **vacia**. El plugin no debe haber modificado
   ningun archivo del repositorio.

8. **Clasificar** la prueba:

   - `approved`: las diez secciones pueden reconstruirse y
     `git status --short` esta vacio.
   - `failed`: alguna seccion falta, o `git status --short` muestra
     cambios atribuibles al plugin.
   - `inconclusive`: la compactacion no se disparo por umbral ni por
     comando soportado en la sesion de prueba.

9. **Registrar manualmente** la evaluacion usando el registrador
   opt-in:

   ```bash
   uv run python tools/ai/record_evaluation.py \
       --task "compact-test del plugin structured-compaction" \
       --agent implementer \
       --model <modelo-id> \
       --provider <proveedor> \
       --result approved|failed|inconclusive \
       --duration-minutes <minutos> \
       --notes "<detalle de la prueba>" \
       --output docs/ai/evaluations.md \
       --write
   ```

   No existe `--prompt` por diseno. No pegar el contenido del fixture
   en ningun campo.

10. **No modificar ADR ni `docs/current-state.md` automaticamente.**
    Si la prueba revela un hallazgo, registrarlo en `docs/mistakes.md`
    o proponer una nueva ADR segun corresponda. La unidad de prueba
    misma queda descrita en este comando.

## Limites declarados

- Este comando es **manual**. No hay mecanismo automatico para
  dispararlo: depende del LLM o del usuario que lo invoque.
- La clasificacion `inconclusive` no es un fallo de la prueba: es el
  resultado esperado cuando OpenCode 1.18.4 no expone un mecanismo
  soportado para forzar compactacion.
- El plugin **no** modifica `docs/current-state.md` ni `docs/decisions.md`.
  Si el resumen recuperado menciona esos archivos, no se ha escrito
  en ellos; cualquier persistencia debe pasar por `/handoff`.