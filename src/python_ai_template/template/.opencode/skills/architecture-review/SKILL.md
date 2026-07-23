# architecture-review

Skill para revisar decisiones y cambios arquitectónicos. Carga esta skill antes de proponer o aprobar cambios que afecten a límites, dependencias, API o configuración de herramientas.

## Cuándo cargar

- Proponer un cambio de límites entre módulos o capas.
- Introducir, actualizar o eliminar una dependencia (runtime o de desarrollo).
- Cambiar la API pública del paquete.
- Migrar de stack, framework, gestor o herramienta canónica.
- Evaluar el impacto de una decisión documentada en `docs/decisions.md`.
- Revisar un PR o diff con posibles consecuencias arquitectónicas.

## Criterios de revisión

Para cada cambio propuesto, evaluar explícitamente:

1. **Límites**: ¿qué módulo o capa añade, modifica o rompe? ¿Se mantiene la separación vigente descrita en `docs/architecture.md`?
2. **Acoplamiento**: ¿qué aumentan los acoplamientos entre módulos, con el exterior o con dependencias? ¿Se introduce acoplamiento cíclico, oculto o implícito?
3. **Reversibilidad**: ¿qué tan fácil es revertir el cambio si la decisión resulta incorrecta? Marcar como **fácil**, **difícil** o **irreversible**.
4. **Compatibilidad**: ¿rompe consumidores existentes, contratos, formatos, interfaces o expectativas de configuración?
5. **Costo de migración**: ¿qué hay que mover, reescribir, reentrenar, revalidar o documentar para adoptarlo?
6. **Riesgos**: listar al menos tres riesgos concretos y, para cada uno, una mitigación posible.

## Diferenciación obligatoria

En cada hallazgo distinguir explícitamente entre:

- **Hecho**: afirmación verificable en el código o configuración actual.
- **Inferencia**: conclusión razonable pero no verificada directamente.
- **Recomendación**: acción sugerida que debe aprobar el usuario.

No presentar inferencias como hechos ni recomendaciones como obligaciones.

## Reglas

- No proponer cambios arquitectónicos amplios sin un plan aprobado por el usuario.
- No introducir dependencias nuevas sin justificación y entrada en `docs/decisions.md`.
- No romper compatibilidad sin documentar el motivo y el plan de migración.
- No hacer commits.
- No usar esta skill como sustituto de `/verify` o de los quality gates: la revisión arquitectónica es complementaria, no reemplazable.

## Documentos a consultar

- `AGENTS.md`: reglas obligatorias.
- `docs/architecture.md`: límites y estructura vigente.
- `docs/decisions.md`: decisiones arquitectónicas previas.
- `docs/mistakes.md`: errores estructurales recurrentes.
- `docs/glossary.md`: terminología del proyecto.
