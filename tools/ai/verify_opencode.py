"""Validador estático de los artefactos de OpenCode para ``python-ai-template``.

Este modulo es el quinto quality gate (ADR-013). Inspecciona un conjunto
cerrado de archivos vigentes del repositorio y exige que satisfagan
invariantes declarados. No compila TypeScript, no ejecuta OpenCode, no
usa red, no modifica archivos y no depende de bibliotecas externas.

Invariantes verificados:

1. Existe
   ``src/python_ai_template/template/.opencode/plugins/structured-compaction.ts``.
2. El plugin importa unicamente
   ``import type { Plugin } from "@opencode-ai/plugin"`` y ningun otro
   modulo.
3. El plugin registra exactamente una vez la clave estructural del hook
   ``experimental.session.compacting``.
4. El plugin contiene exactamente una llamada ejecutable a
   ``output.context.push(...)``.
5. El plugin no contiene ninguna asignacion ejecutable a ``output.prompt``.
6. El plugin no usa filesystem, shell, red, logging ni persistencia.
7. Existen ``.opencode/agents/scout.md``, ``.opencode/commands/review.md``,
   ``.opencode/commands/handoff.md`` y ``.opencode/skills/context-handoff/SKILL.md``.
8. ``docs/current-state.md`` contiene exactamente los 10 encabezados
   canonicos, una vez cada uno, en orden estricto.

Inspeccion textual deliberadamente estrecha
------------------------------------------

La inspeccion es **textual** y **deliberadamente estrecha**. No es un
analisis semantico ni un compilador. Protege la forma estructural del
plugin estatico conocido. Si el plugin crece (mas hooks, mas imports,
logica dinamica), este validador puede requerir actualizacion; eso se
registra en ADR-013.

El scanner lexico pequeño y acotado (``_lex_mask_inert``) reconoce
comentarios ``//`` y ``/* */`` y strings ``'...'``, ``"..."`` y
backticks. Enmascara su contenido a espacios, conserva longitud y
saltos de linea, y respeta escapes (``\\\\``, ``\\"``, ``\\'``,
``\\```). En template literals con ``${...}`` no procesa la
interpolacion: enmascara todo el template literal completo. Esto es
una limitacion declarada: una llamada a ``fetch()`` dentro de una
interpolacion ``${...}`` no se detectaria. El plugin vigente no usa
template literals con interpolacion.

Tres representaciones del codigo:

- **Texto crudo** (``_raw``): se usa para validar imports. Los strings
  se conservan para poder leer el modulo de origen.
- **Texto sin comentarios** (``_no_comments``): se usa para verificar
  la clave estructural del hook ``experimental.session.compacting``.
- **Codigo con comentarios y strings enmascarados** (``_executable``):
  se usa para contar ``output.context.push``, detectar asignacion a
  ``output.prompt`` y detectar tokens prohibidos (filesystem, shell,
  red, logging, persistencia). En esta representacion, una mencion
  dentro de un string o de un comentario aparece como espacios y no
  dispara ninguna regla.

Politica de imports (texto crudo, no en ``_executable``):

- Modulos prohibidos: ``node:fs``, ``node:fs/promises``, ``node:path``,
  ``node:http``, ``node:https``, ``node:net``, ``child_process``,
  ``BunShell``, cualquier modulo que no sea ``@opencode-ai/plugin``.
- Forma esperada: ``import type { Plugin } from "@opencode-ai/plugin"``
  con tolerancia a whitespace y un ``;`` opcional.

Politica de red (codigo ejecutable):

- Se detecta ``fetch(`` como token ejecutable.
- **No** se buscan subcadenas ``http`` o ``https``.
- El bloqueo de modulos de red se hace por politica de imports, no
  por substring.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

PLUGIN_REPO_PATH = (
    Path("src")
    / "python_ai_template"
    / "template"
    / ".opencode"
    / "plugins"
    / "structured-compaction.ts"
)
TEMPLATE_OPENCODE_ROOT = Path("src") / "python_ai_template" / "template" / ".opencode"
SCOUT_PATH = (
    Path("src")
    / "python_ai_template"
    / "template"
    / ".opencode"
    / "agents"
    / "scout.md"
)
REVIEW_COMMAND_PATH = (
    Path("src")
    / "python_ai_template"
    / "template"
    / ".opencode"
    / "commands"
    / "review.md"
)
HANDOFF_COMMAND_PATH = (
    Path("src")
    / "python_ai_template"
    / "template"
    / ".opencode"
    / "commands"
    / "handoff.md"
)
CONTEXT_HANDOFF_SKILL_PATH = (
    Path("src")
    / "python_ai_template"
    / "template"
    / ".opencode"
    / "skills"
    / "context-handoff"
    / "SKILL.md"
)
CURRENT_STATE_PATH = Path("docs") / "current-state.md"

# Pares root <-> template que deben ser byte a byte identicos.
# Politica canonica (ADR-013):
#   src/python_ai_template/template/.opencode/  -> fuente canonica distribuida
#   .opencode/                                  -> copia operativa del repo
# El gate detecta deriva, NO sincroniza.
SYNC_PAIRS: tuple[tuple[Path, Path], ...] = (
    (
        Path(".opencode") / "agents" / "scout.md",
        Path("src")
        / "python_ai_template"
        / "template"
        / ".opencode"
        / "agents"
        / "scout.md",
    ),
    (
        Path(".opencode") / "commands" / "review.md",
        Path("src")
        / "python_ai_template"
        / "template"
        / ".opencode"
        / "commands"
        / "review.md",
    ),
    (
        Path(".opencode") / "commands" / "handoff.md",
        Path("src")
        / "python_ai_template"
        / "template"
        / ".opencode"
        / "commands"
        / "handoff.md",
    ),
    (
        Path(".opencode") / "commands" / "verify.md",
        Path("src")
        / "python_ai_template"
        / "template"
        / ".opencode"
        / "commands"
        / "verify.md",
    ),
    (
        Path(".opencode") / "commands" / "compact-test.md",
        Path("src")
        / "python_ai_template"
        / "template"
        / ".opencode"
        / "commands"
        / "compact-test.md",
    ),
    (
        Path(".opencode") / "skills" / "context-handoff" / "SKILL.md",
        Path("src")
        / "python_ai_template"
        / "template"
        / ".opencode"
        / "skills"
        / "context-handoff"
        / "SKILL.md",
    ),
    (
        Path(".opencode") / "plugins" / "structured-compaction.ts",
        Path("src")
        / "python_ai_template"
        / "template"
        / ".opencode"
        / "plugins"
        / "structured-compaction.ts",
    ),
)

EXPECTED_HEADINGS: tuple[str, ...] = (
    "Objetivo actual",
    "Estado de la tarea",
    "Hechos verificados",
    "Decisiones adoptadas",
    "Archivos modificados",
    "Validaciones ejecutadas",
    "Errores pendientes",
    "Enfoques rechazados y motivo",
    "Divergencias detectadas",
    "Siguiente acción concreta",
)

PLUGIN_REQUIRED_IMPORT = "@opencode-ai/plugin"

# Tokens ejecutables prohibidos (sobre la representacion _executable).
# Las menciones dentro de strings o comentarios ya estan enmascaradas.
FORBIDDEN_EXEC_TOKENS: tuple[str, ...] = (
    # filesystem
    "readFile",
    "writeFile",
    "readdir",
    "unlink",
    "mkdir",
    # shell
    "BunShell",
    "child_process",
    "spawnSync",
    "execSync",
    # red
    "fetch",
    "axios",
    "WebSocket",
    # logging
    "console.log",
    "console.error",
    "console.warn",
    "console.info",
    "console.debug",
    # persistencia y stdout/stderr
    "fs.writeSync",
    "fs.appendFile",
    "process.stdout",
    "process.stderr",
)

# Numero exacto de comprobaciones que se imprimen en el resumen OK.
# Debe coincidir con las lineas [ok] en _report().
TOTAL_OK_CHECKS = 8

# Imports prohibidos (sobre texto crudo). Se valida el modulo origen.
FORBIDDEN_IMPORT_MODULES: tuple[str, ...] = (
    "node:fs",
    "node:fs/promises",
    "node:path",
    "node:http",
    "node:https",
    "node:net",
    "node:child_process",
    "child_process",
    "BunShell",
)


@dataclass(frozen=True)
class Issue:
    """Invariante que falla o anotacion."""

    area: str
    message: str


# ---------------------------------------------------------------------------
# Scanner lexico
# ---------------------------------------------------------------------------


def lex_mask_inert(source: str) -> str:
    """Devuelve una copia del codigo con comentarios y strings enmascarados.

    - Comentarios ``// ... \\n``: enmascarados a espacios, conserva ``\\n``.
    - Comentarios ``/* ... */``: enmascarados a espacios, conserva ``\\n``.
    - Strings ``'...'`` y ``"..."``: contenido enmascarado a espacios,
      delimitadores conservados, escapes respetados.
    - Template literals `` `...` ``: contenido enmascarado a espacios,
      delimitadores conservados, escapes respetados. La interpolacion
      ``${ ... }`` NO se procesa recursivamente: el template literal
      completo queda enmascarado. Esta es una limitacion declarada.

    La longitud de salida es identica a la entrada. Las posiciones de
    inicio de linea se conservan.
    """
    out = list(source)
    n = len(source)
    i = 0
    while i < n:
        c = source[i]
        nxt = source[i + 1] if i + 1 < n else ""

        # Comentario de linea
        if c == "/" and nxt == "/":
            j = i + 2
            while j < n and source[j] != "\n":
                out[j] = " "
                j += 1
            i = j
            continue

        # Comentario de bloque
        if c == "/" and nxt == "*":
            j = i + 2
            while j < n - 1 and not (source[j] == "*" and source[j + 1] == "/"):
                if source[j] != "\n":
                    out[j] = " "
                j += 1
            if j < n - 1:
                out[j] = " "
                out[j + 1] = " "
                i = j + 2
            else:
                i = n
            continue

        # String con comillas dobles
        if c == '"':
            j = i + 1
            while j < n and source[j] != '"':
                if source[j] == "\\" and j + 1 < n:
                    out[j] = " "
                    j += 1
                    if source[j] != "\n":
                        out[j] = " "
                    j += 1
                    continue
                if source[j] != "\n":
                    out[j] = " "
                j += 1
            if j < n:
                # delim out[j] se conserva
                j += 1
            i = j
            continue

        # String con comillas simples
        if c == "'":
            j = i + 1
            while j < n and source[j] != "'":
                if source[j] == "\\" and j + 1 < n:
                    out[j] = " "
                    j += 1
                    if source[j] != "\n":
                        out[j] = " "
                    j += 1
                    continue
                if source[j] != "\n":
                    out[j] = " "
                j += 1
            if j < n:
                j += 1
            i = j
            continue

        # Template literal
        if c == "`":
            j = i + 1
            while j < n and source[j] != "`":
                if source[j] == "\\" and j + 1 < n:
                    out[j] = " "
                    j += 1
                    if source[j] != "\n":
                        out[j] = " "
                    j += 1
                    continue
                if source[j] != "\n":
                    out[j] = " "
                j += 1
            if j < n:
                j += 1
            i = j
            continue

        i += 1
    return "".join(out)


def strip_comments_only(source: str) -> str:
    """Devuelve una copia con comentarios enmascarados y strings intactos.

    - Enmascara ``// ... \\n`` y ``/* ... */`` a espacios.
    - Los strings ``'...'``, ``"..."`` y `` `...` `` se saltan sin
      modificarlos, para no tratar un ``//`` dentro de un string como
      inicio de comentario.
    - Conserva longitud, indices y saltos de linea.

    Se usa para verificar la clave estructural del hook
    ``experimental.session.compacting``.
    """
    out = list(source)
    n = len(source)
    i = 0
    while i < n:
        c = source[i]
        nxt = source[i + 1] if i + 1 < n else ""

        # Saltar strings para no malinterpretar su contenido
        if c == '"' or c == "'" or c == "`":
            quote = c
            j = i + 1
            while j < n and source[j] != quote:
                if source[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                j += 1
            i = j + 1 if j < n else n
            continue

        if c == "/" and nxt == "/":
            j = i + 2
            while j < n and source[j] != "\n":
                out[j] = " "
                j += 1
            i = j
            continue
        if c == "/" and nxt == "*":
            j = i + 2
            while j < n - 1 and not (source[j] == "*" and source[j + 1] == "/"):
                if source[j] != "\n":
                    out[j] = " "
                j += 1
            if j < n - 1:
                out[j] = " "
                out[j + 1] = " "
                i = j + 2
            else:
                i = n
            continue
        i += 1
    return "".join(out)


# ---------------------------------------------------------------------------
# Helpers de inspeccion
# ---------------------------------------------------------------------------


def _module_of_import(stmt: str) -> str:
    """Extrae el modulo de un import de la forma ``... from "X"`` o ``... from 'X'``.

    Devuelve la cadena entre comillas, o vacia si no se reconoce.
    """
    m = re.search(r'from\s+["\']([^"\']+)["\']', stmt)
    return m.group(1) if m else ""


def check_imports(source: str) -> list[Issue]:
    """Valida los imports del plugin sobre texto crudo.

    Reglas:
    - Debe existir exactamente un import con forma
      ``import type { Plugin } from "@opencode-ai/plugin"``
      (con tolerancia a whitespace y ``;`` opcional).
    - No debe haber otros imports, ni de otros paquetes ni de tipos
      adicionales.
    """
    issues: list[Issue] = []
    lines = source.splitlines()
    import_lines = [ln for ln in lines if re.search(r"\bimport\b", ln)]

    expected = re.compile(
        r"""^\s*import\s+type\s*\{\s*Plugin\s*\}\s*from\s*["']"""
        + re.escape(PLUGIN_REQUIRED_IMPORT)
        + r"""["']\s*;?\s*$"""
    )

    if len(import_lines) == 0:
        issues.append(
            Issue(
                area="imports",
                message=(
                    "no se encontro ningun import; se esperaba "
                    f"'import type {{ Plugin }} from "
                    f'"{PLUGIN_REQUIRED_IMPORT}"\''
                ),
            )
        )
        return issues

    plugin_imports = [ln for ln in import_lines if expected.match(ln)]
    if len(plugin_imports) == 0:
        issues.append(
            Issue(
                area="imports",
                message=(
                    "no se encontro el import esperado del tipo Plugin "
                    f"desde {PLUGIN_REQUIRED_IMPORT!r}"
                ),
            )
        )

    for ln in import_lines:
        mod = _module_of_import(ln)
        if not mod:
            issues.append(
                Issue(
                    area="imports",
                    message=f"import sin modulo reconocible: {ln.strip()!r}",
                )
            )
            continue
        if mod != PLUGIN_REQUIRED_IMPORT:
            if mod in FORBIDDEN_IMPORT_MODULES:
                issues.append(
                    Issue(
                        area="imports",
                        message=(
                            f"import de modulo prohibido detectado: "
                            f"{mod!r} en linea: {ln.strip()!r}"
                        ),
                    )
                )
            else:
                issues.append(
                    Issue(
                        area="imports",
                        message=(
                            "import de modulo no permitido: "
                            f"{mod!r} (solo se permite "
                            f"{PLUGIN_REQUIRED_IMPORT!r})"
                        ),
                    )
                )

    return issues


def _check_hook_key(source: str) -> list[Issue]:
    """Verifica la clave estructural del hook sobre texto sin comentarios."""
    issues: list[Issue] = []
    no_comments = strip_comments_only(source)
    pattern = re.compile(r"experimental\.session\.compacting")
    matches = pattern.findall(no_comments)
    if len(matches) == 0:
        issues.append(
            Issue(
                area="plugin",
                message=(
                    "el plugin no registra la clave estructural "
                    "'experimental.session.compacting'"
                ),
            )
        )
    elif len(matches) > 1:
        issues.append(
            Issue(
                area="plugin",
                message=(
                    f"la clave 'experimental.session.compacting' aparece "
                    f"{len(matches)} veces; se esperaba exactamente 1"
                ),
            )
        )
    return issues


def _count_executable_calls(executable: str, name: str) -> int:
    """Cuenta llamadas ejecutables ``name(`` en representacion ejecutable.

    Usa word-boundary a la izquierda y un ``(`` inmediatamente a la
    derecha. Esto evita contar ``output.context.push`` cuando se busca
    ``push``, y tambien evita falsos positivos cuando ``fetch`` aparece
    como parte de un identificador mas largo (p. ej. ``refetch``).
    """
    pattern = re.compile(r"(?<![\w$.])" + re.escape(name) + r"\s*\(")
    return len(pattern.findall(executable))


def check_executable_shape(executable: str) -> list[Issue]:
    """Valida la forma ejecutable del plugin sobre representacion enmascarada."""
    issues: list[Issue] = []

    push_count = _count_executable_calls(executable, "output.context.push")
    if push_count == 0:
        issues.append(
            Issue(
                area="plugin",
                message=(
                    "el plugin no contiene ninguna llamada ejecutable a "
                    "'output.context.push(...)'"
                ),
            )
        )
    elif push_count > 1:
        issues.append(
            Issue(
                area="plugin",
                message=(
                    f"el plugin contiene {push_count} llamadas ejecutables "
                    "a 'output.context.push(...)'; se esperaba exactamente 1"
                ),
            )
        )

    assign = re.compile(r"output\.prompt\s*=[^=]")
    if assign.search(executable):
        issues.append(
            Issue(
                area="plugin",
                message=(
                    "el plugin contiene una asignacion ejecutable a "
                    "'output.prompt'; el plugin solo debe agregar a "
                    "'output.context'"
                ),
            )
        )

    for token in FORBIDDEN_EXEC_TOKENS:
        # word boundary a la izquierda, sin requerir ( justo despues para
        # tokens que ya contienen delimitador (p. ej. console.log).
        # Para tokens tipo 'fetch', exigimos ( para no contar 'fetched'.
        if token in ("fetch", "axios"):
            if _count_executable_calls(executable, token) > 0:
                issues.append(
                    Issue(
                        area="plugin",
                        message=(
                            f"uso ejecutable de {token!r} detectado; "
                            "el plugin no debe usar la red"
                        ),
                    )
                )
        else:
            pattern = re.compile(r"(?<![\w$])" + re.escape(token))
            if pattern.search(executable):
                issues.append(
                    Issue(
                        area="plugin",
                        message=(
                            f"token prohibido detectado en codigo ejecutable: {token!r}"
                        ),
                    )
                )

    return issues


def verify_plugin(repo_root: Path) -> list[Issue]:
    """Verifica el plugin estructurado en ``repo_root``.

    Devuelve una lista (posiblemente vacia) de ``Issue``.
    """
    plugin_path = repo_root / PLUGIN_REPO_PATH
    if not plugin_path.is_file():
        return [
            Issue(
                area="plugin",
                message=f"el plugin no existe en {PLUGIN_REPO_PATH}",
            )
        ]

    raw = plugin_path.read_text(encoding="utf-8")
    executable = lex_mask_inert(raw)

    issues: list[Issue] = []
    issues.extend(check_imports(raw))
    issues.extend(_check_hook_key(raw))
    issues.extend(check_executable_shape(executable))
    return issues


def verify_agent_files(repo_root: Path) -> list[Issue]:
    """Verifica la existencia de los archivos de agente/comando/skill."""
    issues: list[Issue] = []
    paths = (
        (SCOUT_PATH, "scout"),
        (REVIEW_COMMAND_PATH, "review"),
        (HANDOFF_COMMAND_PATH, "handoff"),
        (CONTEXT_HANDOFF_SKILL_PATH, "context-handoff"),
    )
    for rel, label in paths:
        full = repo_root / rel
        if not full.is_file():
            issues.append(
                Issue(
                    area=label,
                    message=f"archivo requerido ausente: {rel}",
                )
            )
            continue
        try:
            content = full.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(
                Issue(
                    area=label,
                    message=f"no se pudo leer {rel}: {exc}",
                )
            )
            continue
        if not content.strip():
            issues.append(
                Issue(
                    area=label,
                    message=f"archivo vacio: {rel}",
                )
            )
    return issues


def verify_current_state(repo_root: Path) -> list[Issue]:
    """Verifica los 10 encabezados canonicos de ``docs/current-state.md``."""
    path = repo_root / CURRENT_STATE_PATH
    if not path.is_file():
        return [
            Issue(
                area="headings",
                message=f"archivo ausente: {CURRENT_STATE_PATH}",
            )
        ]

    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"^## (.+)$", flags=re.MULTILINE)
    found = pattern.findall(text)

    issues: list[Issue] = []
    if found != list(EXPECTED_HEADINGS):
        issues.append(
            Issue(
                area="headings",
                message=(
                    "los encabezados de "
                    f"{CURRENT_STATE_PATH} no coinciden con los 10 "
                    "canonicos en orden estricto"
                ),
            )
        )
        # Diagnostico adicional: que falta o sobra
        expected_set = set(EXPECTED_HEADINGS)
        found_set = set(found)
        missing = expected_set - found_set
        extra = found_set - expected_set
        if missing:
            issues.append(
                Issue(
                    area="headings",
                    message=(
                        "encabezados canonicos ausentes: " + ", ".join(sorted(missing))
                    ),
                )
            )
        if extra:
            issues.append(
                Issue(
                    area="headings",
                    message=(
                        "encabezados adicionales presentes: " + ", ".join(sorted(extra))
                    ),
                )
            )
        duplicates = sorted({h for h in found if found.count(h) > 1})
        if duplicates:
            issues.append(
                Issue(
                    area="headings",
                    message=("encabezados duplicados: " + ", ".join(duplicates)),
                )
            )
    return issues


def verify_sync(repo_root: Path) -> list[Issue]:
    """Comprueba que cada par root<->template existe en ambos lados y es
    byte a byte identico. Solo detecta deriva; no sincroniza.
    """
    issues: list[Issue] = []
    for root_rel, tpl_rel in SYNC_PAIRS:
        root_path = repo_root / root_rel
        tpl_path = repo_root / tpl_rel
        if not root_path.is_file():
            issues.append(
                Issue(
                    area="sync",
                    message=f"falta en raiz: {root_rel}",
                )
            )
            continue
        if not tpl_path.is_file():
            issues.append(
                Issue(
                    area="sync",
                    message=f"falta en template: {tpl_rel}",
                )
            )
            continue
        if root_path.read_bytes() != tpl_path.read_bytes():
            issues.append(
                Issue(
                    area="sync",
                    message=f"{root_rel} difiere de {tpl_rel}",
                )
            )
    return issues


def verify_all(repo_root: Path) -> list[Issue]:
    """Ejecuta todas las verificaciones y devuelve la lista agregada de issues."""
    issues: list[Issue] = []
    issues.extend(verify_plugin(repo_root))
    issues.extend(verify_agent_files(repo_root))
    issues.extend(verify_current_state(repo_root))
    issues.extend(verify_sync(repo_root))
    return issues


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------


def _report(issues: list[Issue]) -> int:
    """Imprime el reporte y devuelve el exit code."""
    print("Validacion estatica de OpenCode (ADR-013)")
    print("=" * 72)

    if not issues:
        print("[ok] plugin: import unico desde @opencode-ai/plugin")
        print("[ok] plugin: hook experimental.session.compacting registrado")
        print("[ok] plugin: una llamada ejecutable a output.context.push")
        print("[ok] plugin: ninguna asignacion ejecutable a output.prompt")
        print("[ok] plugin: ausencia de filesystem, shell, red, logging, persistencia")
        print("[ok] archivos: scout, review, handoff, context-handoff presentes")
        print(
            "[ok] headings: docs/current-state.md con 10 encabezados canonicos en orden"
        )
        print("[ok] sync: pares root<->template byte a byte identicos")
        print("=" * 72)
        print(f"OK: invariantes verificados ({TOTAL_OK_CHECKS}/{TOTAL_OK_CHECKS})")
        return 0

    for issue in issues:
        print(f"[error] {issue.area}: {issue.message}")
    print("=" * 72)
    print(f"FALLIDO: {len(issues)} invariantes no verificados")
    return 1


def resolve_repo_root() -> Path:
    """Resuelve la raiz del repositorio desde la ubicacion de este archivo.

    ``tools/ai/verify_opencode.py`` -> ``tools/ai/`` -> ``tools/`` -> raiz.
    """
    return Path(__file__).resolve().parents[2]


def main() -> int:
    repo_root = resolve_repo_root()
    issues = verify_all(repo_root)
    return _report(issues)


if __name__ == "__main__":
    sys.exit(main())
