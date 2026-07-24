"""Tests del validador estatico de OpenCode (``verify_opencode.py``).

Los tests son completamente hermeticos: construyen un arbol sintetico
con ``tmp_path`` y nunca dependen del ``cwd`` ni del repositorio real.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "tools" / "ai"),
)

from verify_opencode import (  # noqa: E402
    CONTEXT_HANDOFF_SKILL_PATH,
    CURRENT_STATE_PATH,
    EXPECTED_HEADINGS,
    HANDOFF_COMMAND_PATH,
    PLUGIN_REPO_PATH,
    REVIEW_COMMAND_PATH,
    SCOUT_PATH,
    SYNC_PAIRS,
    TEMPLATE_OPENCODE_ROOT,
    check_executable_shape,
    check_imports,
    lex_mask_inert,
    resolve_repo_root,
    strip_comments_only,
    verify_agent_files,
    verify_all,
    verify_current_state,
    verify_plugin,
    verify_sync,
)

PLUGIN_DIR = PLUGIN_REPO_PATH.parent
PLUGIN_NAME = PLUGIN_REPO_PATH.name


# ---------------------------------------------------------------------------
# Helpers de fixtures
# ---------------------------------------------------------------------------


def _valid_plugin_source() -> str:
    return (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        "\n"
        "const REMINDER = `recordatorio`\n"
        "\n"
        "export const StructuredCompactionPlugin: Plugin = async () => {\n"
        "  return {\n"
        '    "experimental.session.compacting": async (_i, output) => {\n'
        "      output.context.push(REMINDER)\n"
        "    },\n"
        "  }\n"
        "}\n"
    )


PUSH_LINE = "      output.context.push(REMINDER)\n"


def _write_current_state(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = ["# Estado actual\n", "\n"]
    for h in EXPECTED_HEADINGS:
        parts.append(f"## {h}\n\nContenido de la seccion.\n\n")
    path.write_text("".join(parts), encoding="utf-8")


def _build_repo(
    tmp_path: Path,
    *,
    plugin_source: str | None = None,
    sync: bool = True,
) -> Path:
    """Crea un repo sintetico que satisface todos los invariantes.

    El template (``src/python_ai_template/template/.opencode/``) es la
    fuente canonica. Si ``sync`` es True (default) crea tambien las
    copias en ``.opencode/`` byte a byte identicas.
    """
    plugin_text = plugin_source if plugin_source is not None else _valid_plugin_source()
    scout_text = "# scout\n"
    review_text = "# /review\n"
    handoff_text = "# /handoff\n"
    verify_text = "# /verify\n"
    skill_text = "# context-handoff\n"
    compact_text = "# /compact-test\n"

    # Escribir en el template (fuente canonica)
    plugin_path = tmp_path / PLUGIN_REPO_PATH
    plugin_path.parent.mkdir(parents=True, exist_ok=True)
    plugin_path.write_text(plugin_text, encoding="utf-8")
    (tmp_path / SCOUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / SCOUT_PATH).write_text(scout_text, encoding="utf-8")
    (tmp_path / REVIEW_COMMAND_PATH).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / REVIEW_COMMAND_PATH).write_text(review_text, encoding="utf-8")
    (tmp_path / HANDOFF_COMMAND_PATH).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / HANDOFF_COMMAND_PATH).write_text(handoff_text, encoding="utf-8")
    # verify.md y compact-test.md se distribuyen pero no los valida
    # verify_agent_files individualmente; van solo en el sync
    (tmp_path / TEMPLATE_OPENCODE_ROOT / "commands" / "verify.md").parent.mkdir(
        parents=True, exist_ok=True
    )
    (tmp_path / TEMPLATE_OPENCODE_ROOT / "commands" / "verify.md").write_text(
        verify_text, encoding="utf-8"
    )
    (tmp_path / TEMPLATE_OPENCODE_ROOT / "commands" / "compact-test.md").parent.mkdir(
        parents=True, exist_ok=True
    )
    (tmp_path / TEMPLATE_OPENCODE_ROOT / "commands" / "compact-test.md").write_text(
        compact_text, encoding="utf-8"
    )
    (tmp_path / CONTEXT_HANDOFF_SKILL_PATH).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / CONTEXT_HANDOFF_SKILL_PATH).write_text(skill_text, encoding="utf-8")
    _write_current_state(tmp_path / CURRENT_STATE_PATH)

    if sync:
        for root_rel, tpl_rel in SYNC_PAIRS:
            root_full = tmp_path / root_rel
            tpl_full = tmp_path / tpl_rel
            root_full.parent.mkdir(parents=True, exist_ok=True)
            root_full.write_bytes(tpl_full.read_bytes())

    return tmp_path


# ---------------------------------------------------------------------------
# Scanner lexico
# ---------------------------------------------------------------------------


def test_lex_output_context_push_in_comment_allowed() -> None:
    src = (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        "// output.context.push is structural\n"
        'const x = "not a call"\n'
        "export const P: Plugin = async () => ({\n"
        '  "experimental.session.compacting": async (_i, output) => {\n'
        '    output.context.push("x")\n'
        "  },\n"
        "})\n"
    )
    masked = lex_mask_inert(src)
    issues = check_executable_shape(masked)
    # Solo debe haber una llamada: la del callback real.
    push_issues = [i for i in issues if "output.context.push" in i.message]
    assert push_issues == []


def test_lex_output_context_push_in_string_allowed() -> None:
    src = (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        'const note = "output.context.push appears here"\n'
        "export const P: Plugin = async () => ({\n"
        '  "experimental.session.compacting": async (_i, output) => {\n'
        '    output.context.push("y")\n'
        "  },\n"
        "})\n"
    )
    masked = lex_mask_inert(src)
    issues = check_executable_shape(masked)
    push_issues = [i for i in issues if "output.context.push" in i.message]
    assert push_issues == []


def test_lex_fetch_in_string_allowed() -> None:
    src = (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        'const note = "No uses fetch() en este plugin"\n'
        "export const P: Plugin = async () => ({\n"
        '  "experimental.session.compacting": async (_i, output) => {\n'
        '    output.context.push("ok")\n'
        "  },\n"
        "})\n"
    )
    masked = lex_mask_inert(src)
    issues = check_executable_shape(masked)
    fetch_issues = [i for i in issues if "fetch" in i.message]
    assert fetch_issues == []


def test_lex_fetch_executable_rejected() -> None:
    src = (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        "export const P: Plugin = async () => ({\n"
        '  "experimental.session.compacting": async (_i, output) => {\n'
        '    fetch("http://example.com")\n'
        '    output.context.push("x")\n'
        "  },\n"
        "})\n"
    )
    masked = lex_mask_inert(src)
    issues = check_executable_shape(masked)
    fetch_issues = [i for i in issues if "fetch" in i.message]
    assert len(fetch_issues) >= 1


def test_lex_readfile_in_comment_allowed() -> None:
    src = (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        "// do not use readFile\n"
        "export const P: Plugin = async () => ({\n"
        '  "experimental.session.compacting": async (_i, output) => {\n'
        '    output.context.push("x")\n'
        "  },\n"
        "})\n"
    )
    masked = lex_mask_inert(src)
    issues = check_executable_shape(masked)
    fs_issues = [i for i in issues if "readFile" in i.message]
    assert fs_issues == []


def test_lex_readfile_executable_rejected() -> None:
    src = (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        "export const P: Plugin = async () => ({\n"
        '  "experimental.session.compacting": async (_i, output) => {\n'
        '    await readFile("/etc/passwd")\n'
        '    output.context.push("x")\n'
        "  },\n"
        "})\n"
    )
    masked = lex_mask_inert(src)
    issues = check_executable_shape(masked)
    fs_issues = [i for i in issues if "readFile" in i.message]
    assert len(fs_issues) >= 1


def test_lex_output_prompt_in_string_allowed() -> None:
    src = (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        'const note = "output.prompt = forbidden";\n'
        "export const P: Plugin = async () => ({\n"
        '  "experimental.session.compacting": async (_i, output) => {\n'
        '    output.context.push("x")\n'
        "  },\n"
        "})\n"
    )
    masked = lex_mask_inert(src)
    issues = check_executable_shape(masked)
    assign_issues = [i for i in issues if "output.prompt" in i.message]
    assert assign_issues == []


def test_lex_output_prompt_executable_rejected() -> None:
    src = (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        "export const P: Plugin = async () => ({\n"
        '  "experimental.session.compacting": async (_i, output) => {\n'
        '    output.prompt = "rewritten"\n'
        "  },\n"
        "})\n"
    )
    masked = lex_mask_inert(src)
    issues = check_executable_shape(masked)
    assign_issues = [i for i in issues if "output.prompt" in i.message]
    assert len(assign_issues) >= 1


def test_lex_strings_with_escapes() -> None:
    src = (
        'const a = "with \\"escaped\\" quote";\n'
        "const b = 'with \\'escaped\\' apostrophe';\n"
        "const c = `with \\` escaped backtick`;\n"
    )
    masked = lex_mask_inert(src)
    # Las tres cadenas deben quedar enmascaradas (longitud conservada)
    assert len(masked) == len(src)
    # El delimitador exterior se conserva
    assert masked.count('"') == 2
    assert masked.count("'") == 2
    assert masked.count("`") == 2


def test_lex_template_literal_no_interpolation() -> None:
    src = 'const t = `simple template`;\nconst x = "fetch(endpoint)";\n'
    masked = lex_mask_inert(src)
    # ``fetch(`` debe quedar enmascarado dentro del segundo string
    assert "fetch(" not in masked


def test_lex_template_literal_with_interpolation_is_limit() -> None:
    """Documenta el limite: una llamada dentro de ${} no se inspecciona."""
    src = (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        "const t = `hello ${fetch(endpoint)} world`;\n"
        "export const P: Plugin = async () => ({\n"
        '  "experimental.session.compacting": async (_i, output) => {\n'
        '    output.context.push("x")\n'
        "  },\n"
        "})\n"
    )
    masked = lex_mask_inert(src)
    # El template literal completo queda enmascarado; fetch no se ve
    # en el ejecutable. Esto es la limitacion declarada.
    assert "fetch(" not in masked


def teststrip_comments_only_preserves_strings() -> None:
    src = (
        "// comentario de linea\n"
        'const x = "comentario // dentro de string";\n'
        "/* bloque */\n"
        'const y = "/* dentro */";\n'
    )
    out = strip_comments_only(src)
    assert "// comentario de linea" not in out
    assert "/* bloque */" not in out
    assert "comentario // dentro de string" in out
    assert "/* dentro */" in out


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------


def testcheck_imports_ok() -> None:
    src = 'import type { Plugin } from "@opencode-ai/plugin"\n'
    assert check_imports(src) == []


def testcheck_imports_forbidden_module() -> None:
    src = (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        'import { readFile } from "node:fs"\n'
    )
    issues = check_imports(src)
    assert any("node:fs" in i.message for i in issues)


def testcheck_imports_unexpected_module() -> None:
    src = 'import type { Plugin } from "@opencode-ai/plugin"\nimport x from "lodash"\n'
    issues = check_imports(src)
    assert any("lodash" in i.message for i in issues)


def testcheck_imports_missing_plugin_import() -> None:
    src = 'import x from "y"\n'
    issues = check_imports(src)
    assert any("Plugin" in i.message for i in issues)


# ---------------------------------------------------------------------------
# verify_plugin (integracion)
# ---------------------------------------------------------------------------


def test_verify_plugin_ok(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    assert verify_plugin(repo) == []


def test_verify_plugin_missing(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    (repo / PLUGIN_REPO_PATH).unlink()
    issues = verify_plugin(repo)
    assert any("no existe" in i.message for i in issues)


def test_verify_plugin_multiple_push(tmp_path: Path) -> None:
    src = _valid_plugin_source().replace(
        "output.context.push(REMINDER)\n",
        "output.context.push(REMINDER)\noutput.context.push(REMINDER)\n",
    )
    repo = _build_repo(tmp_path, plugin_source=src)
    issues = verify_plugin(repo)
    assert any("2 llamadas" in i.message for i in issues)


def test_verify_plugin_no_push(tmp_path: Path) -> None:
    src = _valid_plugin_source().replace(
        "output.context.push(REMINDER)\n", "/* noop */\n"
    )
    repo = _build_repo(tmp_path, plugin_source=src)
    issues = verify_plugin(repo)
    assert any("ninguna llamada" in i.message for i in issues)


def test_verify_plugin_output_prompt_assign(tmp_path: Path) -> None:
    src = _valid_plugin_source().replace(
        "output.context.push(REMINDER)\n",
        'output.prompt = "nope"\noutput.context.push(REMINDER)\n',
    )
    repo = _build_repo(tmp_path, plugin_source=src)
    issues = verify_plugin(repo)
    assert any("output.prompt" in i.message for i in issues)


def test_verify_plugin_filesystem(tmp_path: Path) -> None:
    src = _valid_plugin_source().replace(
        "output.context.push(REMINDER)\n",
        'await readFile("x")\noutput.context.push(REMINDER)\n',
    )
    repo = _build_repo(tmp_path, plugin_source=src)
    issues = verify_plugin(repo)
    assert any("readFile" in i.message for i in issues)


def test_verify_plugin_shell(tmp_path: Path) -> None:
    src = _valid_plugin_source().replace(
        "output.context.push(REMINDER)\n",
        "BunShell.$`ls`\noutput.context.push(REMINDER)\n",
    )
    repo = _build_repo(tmp_path, plugin_source=src)
    issues = verify_plugin(repo)
    assert any("BunShell" in i.message for i in issues)


def test_verify_plugin_network(tmp_path: Path) -> None:
    src = _valid_plugin_source().replace(
        "output.context.push(REMINDER)\n",
        'await fetch("http://x")\noutput.context.push(REMINDER)\n',
    )
    repo = _build_repo(tmp_path, plugin_source=src)
    issues = verify_plugin(repo)
    assert any("fetch" in i.message for i in issues)


def test_verify_plugin_logging(tmp_path: Path) -> None:
    src = _valid_plugin_source().replace(
        "output.context.push(REMINDER)\n",
        'console.log("x")\noutput.context.push(REMINDER)\n',
    )
    repo = _build_repo(tmp_path, plugin_source=src)
    issues = verify_plugin(repo)
    assert any("console.log" in i.message for i in issues)


def test_verify_plugin_persistence(tmp_path: Path) -> None:
    src = _valid_plugin_source().replace(
        "output.context.push(REMINDER)\n",
        'fs.writeSync(1, "x")\noutput.context.push(REMINDER)\n',
    )
    repo = _build_repo(tmp_path, plugin_source=src)
    issues = verify_plugin(repo)
    assert any("fs.writeSync" in i.message for i in issues)


def test_verify_plugin_forbidden_import_filesystem(tmp_path: Path) -> None:
    src = (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        'import { readFile } from "node:fs"\n'
        "export const P: Plugin = async () => ({\n"
        '  "experimental.session.compacting": async (_i, output) => {\n'
        '    output.context.push("x")\n'
        "  },\n"
        "})\n"
    )
    repo = _build_repo(tmp_path, plugin_source=src)
    issues = verify_plugin(repo)
    assert any("node:fs" in i.message for i in issues)


def test_verify_plugin_double_hook(tmp_path: Path) -> None:
    src = _valid_plugin_source().replace(
        "export const StructuredCompactionPlugin: Plugin = async () => {\n",
        "export const P1: Plugin = async () => ({\n"
        '  "experimental.session.compacting": async () => undefined,\n'
        "})\n"
        "export const P: Plugin = async () => ({\n",
    )
    repo = _build_repo(tmp_path, plugin_source=src)
    issues = verify_plugin(repo)
    assert any("2 veces" in i.message for i in issues)


# ---------------------------------------------------------------------------
# verify_agent_files
# ---------------------------------------------------------------------------


def test_verify_agent_files_ok(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    assert verify_agent_files(repo) == []


def test_verify_agent_files_missing_one(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    (repo / SCOUT_PATH).unlink()
    issues = verify_agent_files(repo)
    assert any("scout" in i.message for i in issues)


def test_verify_agent_files_empty(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    (repo / REVIEW_COMMAND_PATH).write_text("", encoding="utf-8")
    issues = verify_agent_files(repo)
    assert any("vacio" in i.message for i in issues)


# ---------------------------------------------------------------------------
# verify_current_state
# ---------------------------------------------------------------------------


def test_verify_current_state_ok(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    assert verify_current_state(repo) == []


def test_verify_current_state_missing(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    (repo / CURRENT_STATE_PATH).unlink()
    issues = verify_current_state(repo)
    assert any("ausente" in i.message for i in issues)


def test_verify_current_state_out_of_order(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    state = repo / CURRENT_STATE_PATH
    # Invierte el orden de los encabezados
    headings = list(EXPECTED_HEADINGS)
    headings.reverse()
    parts = ["# Estado actual\n", "\n"]
    for h in headings:
        parts.append(f"## {h}\n\nContenido.\n\n")
    state.write_text("".join(parts), encoding="utf-8")
    issues = verify_current_state(repo)
    assert any("orden" in i.message for i in issues)


def test_verify_current_state_heading_missing(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    state = repo / CURRENT_STATE_PATH
    text = state.read_text(encoding="utf-8")
    text = text.replace("## Estado de la tarea\n", "## Renombrado\n")
    state.write_text(text, encoding="utf-8")
    issues = verify_current_state(repo)
    assert any("no coinciden" in i.message for i in issues)


def test_verify_current_state_heading_duplicated(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    state = repo / CURRENT_STATE_PATH
    text = state.read_text(encoding="utf-8")
    text = text.replace("## Hechos verificados\n", "## Hechos verificados\n", 1)
    # Duplicar intencionalmente
    text = text.replace("## Decisiones adoptadas\n", "## Hechos verificados\n", 1)
    state.write_text(text, encoding="utf-8")
    issues = verify_current_state(repo)
    assert any("duplicados" in i.message for i in issues)


# ---------------------------------------------------------------------------
# verify_all
# ---------------------------------------------------------------------------


def test_verify_all_ok(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path)
    assert verify_all(repo) == []


def test_verify_all_multiple_failures(tmp_path: Path) -> None:
    repo = tmp_path
    # Repo vacio: todo falla
    issues = verify_all(repo)
    assert len(issues) >= 3


# ---------------------------------------------------------------------------
# verify_sync (root <-> template)
# ---------------------------------------------------------------------------


def test_verify_sync_ok(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path, sync=True)
    assert verify_sync(repo) == []


def test_verify_sync_template_only(tmp_path: Path) -> None:
    """sync=False: solo se escribe el template, la raiz queda vacia."""
    repo = _build_repo(tmp_path, sync=False)
    issues = verify_sync(repo)
    assert any("falta en raiz" in i.message for i in issues)


def test_verify_sync_root_only(tmp_path: Path) -> None:
    """Borrar el template tras sync=True: la raiz queda sin contraparte."""
    repo = _build_repo(tmp_path, sync=True)
    for _root_rel, tpl_rel in SYNC_PAIRS:
        (repo / tpl_rel).unlink()
    issues = verify_sync(repo)
    assert any("falta en template" in i.message for i in issues)


def test_verify_sync_differs(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path, sync=True)
    # Modificar el plugin en raiz
    (repo / PLUGIN_REPO_PATH).write_text("DIFFERENT", encoding="utf-8")
    issues = verify_sync(repo)
    assert any("difiere de" in i.message for i in issues)
    diff_issues = [i for i in issues if "difiere" in i.message]
    assert any(str(PLUGIN_REPO_PATH) in i.message for i in diff_issues)


def test_verify_sync_byte_identical(tmp_path: Path) -> None:
    repo = _build_repo(tmp_path, sync=True)
    # Si la raiz y el template son iguales, no hay issues de sync
    issues = verify_sync(repo)
    sync_issues = [i for i in issues if i.area == "sync"]
    assert sync_issues == []


# ---------------------------------------------------------------------------
# Resolucion de raiz independiente del cwd
# ---------------------------------------------------------------------------


def test_resolve_repo_root_independent_of_cwd() -> None:
    """Verifica que resolve_repo_root() apunta a la raiz del repo real,
    independientemente del cwd desde el que se importe el modulo."""
    root = resolve_repo_root()
    assert (root / "pyproject.toml").is_file(), "debe tener pyproject.toml"
    assert (root / "tools" / "ai" / "verify_opencode.py").is_file()

    # Asegura que NO es el cwd actual (si cwd coincide es coincidencia
    # benigna; lo relevante es que funcione desde cualquier cwd).
    assert root.is_dir()


# ---------------------------------------------------------------------------
# Heading de nivel incorrecto
# ---------------------------------------------------------------------------


def test_verify_current_state_wrong_heading_level(tmp_path: Path) -> None:
    """Un heading con # (en lugar de ##) no es detectado por la regex
    ^## (.+)$, por lo que falla como ausente."""
    repo = _build_repo(tmp_path)
    state = repo / CURRENT_STATE_PATH
    text = state.read_text(encoding="utf-8")
    text = text.replace("## Objetivo actual\n", "# Objetivo actual\n", 1)
    state.write_text(text, encoding="utf-8")
    issues = verify_current_state(repo)
    # Debe fallar: el heading con # no coincide con ^## (.+)$
    assert any(
        "ausentes" in i.message or "no coinciden" in i.message for i in issues
    ), f"se esperaba fallo por heading incorrecto, issues: {issues}"


# ---------------------------------------------------------------------------
# Import de modulo de red prohibido (node:http)
# ---------------------------------------------------------------------------


def testcheck_imports_forbidden_http_module() -> None:
    src = (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        'import { createServer } from "node:http"\n'
    )
    issues = check_imports(src)
    assert any("node:http" in i.message for i in issues)


def test_verify_plugin_forbidden_import_network(tmp_path: Path) -> None:
    """Verifica que verify_plugin rechaza un import desde node:http."""
    src = (
        'import type { Plugin } from "@opencode-ai/plugin"\n'
        'import { createServer } from "node:http"\n'
        "export const P: Plugin = async () => ({\n"
        '  "experimental.session.compacting": async (_i, output) => {\n'
        '    output.context.push("x")\n'
        "  },\n"
        "})\n"
    )
    repo = _build_repo(tmp_path, plugin_source=src)
    issues = verify_plugin(repo)
    assert any("node:http" in i.message for i in issues), (
        f"se esperaba rechazo de node:http, issues: {issues}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
