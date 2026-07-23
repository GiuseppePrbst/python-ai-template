# Evaluaciones de modelos

Registro de evaluaciones concretas de modelos de lenguaje en tareas reales del proyecto. Cada entrada documenta modelo, tarea, resultado, tiempo, correcciones humanas, validaciones y decisión de uso futuro.

No se registran impresiones generales: solo experimentos comparables con una tarea definida y un resultado medible. Una entrada sirve para decidir, en el futuro, qué modelo usar para una tarea parecida.

---

## Plantilla

```markdown
### YYYY-MM-DD — <título corto>

- **Modelo**: id exacto del modelo (por ejemplo `proveedor/modelo-x`).
- **Proveedor**: nombre del proveedor.
- **Interfaz**: interfaz utilizada (por ejemplo OpenCode Web, terminal).
- **Tarea**: descripción concreta de lo que se pidió al modelo.
- **Complejidad**: baja | media | alta.
- **Prompt o entrada**: resumen del prompt o enlace al archivo relevante.
- **Resultado del modelo**: resumen del output y archivos modificados.
- **Tiempo invertido**: estimación del tiempo total de la interacción (incluyendo iteraciones y reintentos).
- **Correcciones humanas**: qué hubo que ajustar manualmente después.
- **Validaciones**: resultado de los quality gates aplicados (`ruff`, `pyright`, `pytest`).
- **Decisión de uso futuro**: repetir con el mismo modelo, escalar a premium, replantear la tarea, etc.
```

---

(El registro está vacío por ahora. La primera entrada se añadirá cuando se complete una evaluación concreta del proyecto.)
