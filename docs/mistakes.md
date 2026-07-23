# Errores recurrentes

Registro de errores recurrentes o con valor futuro. Cada entrada documenta síntoma, causa raíz, corrección y prevención para evitar que se repita.

No se registran errores triviales: ni typos de una vez, ni descuidos puntuales sin patrón, ni errores que no se repetirán. Solo se documenta lo que aporta aprendizaje futuro. El comando `/mistake` aplica este filtro.

---

## Plantilla

```markdown
### YYYY-MM-DD — <título corto>

- **Síntoma**: cómo se manifestó el problema.
- **Causa raíz**: por qué ocurrió, con referencia a archivos o comandos si aplica.
- **Corrección**: qué se cambió para resolverlo.
- **Prevención**: regla, validación, checklist o automatización que evite la repetición.
```

---

### 2026-07-23 — `pyproject.toml` generado usaba el nombre visible como nombre de distribución

- **Síntoma**: la generación con

  ```bash
  --name "E2E Smoke"
  --package e2e_smoke
  ```

  producía en el `pyproject.toml` del proyecto generado:

  ```toml
  [project]
  name = "E2E Smoke"
  ```

  `uv sync` rechazaba el proyecto con un error de metadatos: el nombre de
  distribución no admite espacios.

- **Causa raíz**: se reutilizó `{{PROJECT_NAME}}`, que es un nombre
  **visible**, como nombre técnico de distribución en `[project].name`. Los
  tests verificaban la sustitución textual del placeholder y la estructura
  del árbol generado, pero no validaban la semántica real del proyecto
  generado mediante `uv sync`. Mientras no se ejecuta `uv sync` dentro del
  proyecto generado con datos representativos, este tipo de error pasa los
  tests unitarios.

- **Corrección**: se introdujo un tercer placeholder, `{{DISTRIBUTION_NAME}}`,
  derivado internamente de `{{PACKAGE_NAME}}` mediante:

  ```text
  e2e_smoke -> e2e-smoke
  ```

  La derivación es `package_name.lower().replace("_", "-")` y el resultado se
  valida con la expresión regular:

  ```text
  ^[a-z0-9]+(?:-[a-z0-9]+)*$
  ```

  Si no cumple el patrón, el generador falla antes de escribir. La
  sustitución en `template/pyproject.toml.tmpl` usa
  `{{DISTRIBUTION_NAME}}` para `[project].name`, mientras que las rutas,
  imports y configuración de paquetes siguen usando `{{PACKAGE_NAME}}`. La
  distinción entre los tres nombres se documenta en ADR-008.

- **Prevención**: un generador no se considera terminado hasta:

  1. generar un proyecto independiente con el generador;
  2. usar datos representativos, incluyendo un nombre visible con espacios;
  3. ejecutar dentro del proyecto generado:
     - `uv sync`
     - `uv run ruff check .`
     - `uv run ruff format --check .`
     - `uv run pyright`
     - `uv run pytest`

  Los tests unitarios del generador son necesarios pero **no sustituyen** el
  E2E semántico. La regla queda incorporada a la definición de terminado de
  esta plantilla.
