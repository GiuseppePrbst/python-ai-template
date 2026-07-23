"""Tests para ``tools/new_project.py``."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import new_project  # noqa: E402

PLACEHOLDER_PATTERN = re.compile(r"\{\{[^}]*\}\}")

FORBIDDEN_OPENCODE_NAMES = frozenset(
    {
        "node_modules",
        "package.json",
        "package-lock.json",
        "bun.lock",
        "bun.lockb",
    }
)

SENSITIVE_SUFFIXES = frozenset({".env", ".pem", ".key", ".secret"})


def _list_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file())


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


# 1. Generación exitosa.
def test_generates_project_successfully(tmp_path: Path) -> None:
    dest = tmp_path / "my-project"
    rc = new_project.generate("My Project", "my_project", dest)
    assert rc == 0
    assert dest.is_dir()
    assert (dest / "pyproject.toml").is_file()
    assert (dest / "README.md").is_file()
    assert (dest / "src" / "my_project" / "__init__.py").is_file()
    assert (dest / "tests" / "test_smoke.py").is_file()


# 2. Nombre de proyecto vacío.
def test_empty_name_rejected(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    rc = new_project.generate("", "my_pkg", dest)
    assert rc != 0
    assert not dest.exists()


# 3. Nombre compuesto solo por espacios.
def test_whitespace_only_name_rejected(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    rc = new_project.generate("   ", "my_pkg", dest)
    assert rc != 0
    assert not dest.exists()


# 4. Package con guion.
def test_package_with_dash_rejected(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    rc = new_project.generate("My Project", "mi-pkg", dest)
    assert rc != 0
    assert not dest.exists()


# 5. Package con espacios.
def test_package_with_spaces_rejected(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    rc = new_project.generate("My Project", "mi pkg", dest)
    assert rc != 0
    assert not dest.exists()


# 6. Package con punto.
def test_package_with_dot_rejected(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    rc = new_project.generate("My Project", "mi.pkg", dest)
    assert rc != 0
    assert not dest.exists()


# 7. Package que no sea identificador Python.
def test_package_not_identifier_rejected(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    rc = new_project.generate("My Project", "123abc", dest)
    assert rc != 0
    assert not dest.exists()


# 8. Package que sea keyword de Python.
def test_package_keyword_rejected(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    rc = new_project.generate("My Project", "class", dest)
    assert rc != 0
    assert not dest.exists()


# 9. Destino existente no vacío.
def test_existing_non_empty_destination_rejected(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    dest.mkdir()
    sentinel = dest / "user-data.txt"
    sentinel.write_text("user content - do not touch", encoding="utf-8")
    rc = new_project.generate("My Project", "my_pkg", dest)
    assert rc != 0
    assert sentinel.read_text(encoding="utf-8") == "user content - do not touch"
    assert not (dest / "pyproject.toml").exists()


# 10. Destino existente vacío.
def test_existing_empty_destination_rejected(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    dest.mkdir()
    rc = new_project.generate("My Project", "my_pkg", dest)
    assert rc != 0
    assert dest.is_dir()
    assert not (dest / "pyproject.toml").exists()


# 11. No sobrescritura: una segunda generación sobre el mismo destino falla
# y deja el contenido de la primera intacto.
def test_does_not_overwrite_existing_files(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    assert new_project.generate("My Project", "my_pkg", dest) == 0
    first_pyproject = (dest / "pyproject.toml").read_text(encoding="utf-8")
    first_readme = (dest / "README.md").read_text(encoding="utf-8")
    rc = new_project.generate("Different Project", "different_pkg", dest)
    assert rc != 0
    assert (dest / "pyproject.toml").read_text(encoding="utf-8") == first_pyproject
    assert (dest / "README.md").read_text(encoding="utf-8") == first_readme


# 12. Sustitución de {{PROJECT_NAME}}.
def test_project_name_substitution(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    new_project.generate("My Unique Project", "my_pkg", dest)
    readme = (dest / "README.md").read_text(encoding="utf-8")
    assert "# My Unique Project" in readme
    init = (dest / "src" / "my_pkg" / "__init__.py").read_text(encoding="utf-8")
    assert "My Unique Project package" in init
    smoke = (dest / "tests" / "test_smoke.py").read_text(encoding="utf-8")
    assert "Smoke tests for the My Unique Project package" in smoke


# 13. Sustitución de {{PACKAGE_NAME}}.
def test_package_name_substitution(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    new_project.generate("My Project", "my_unique_pkg", dest)
    init = (dest / "src" / "my_unique_pkg" / "__init__.py").read_text(encoding="utf-8")
    assert '"""My Project package."""' in init
    assert (dest / "src" / "my_unique_pkg" / "__init__.py").is_file()
    pyproject = (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert 'packages = ["src/my_unique_pkg"]' in pyproject
    smoke = (dest / "tests" / "test_smoke.py").read_text(encoding="utf-8")
    assert 'importlib.import_module("my_unique_pkg")' in smoke


# 14. Ausencia de placeholders sin resolver en el proyecto generado.
def test_no_unresolved_placeholders(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    new_project.generate("My Project", "my_pkg", dest)
    for path in _list_files(dest):
        text = path.read_text(encoding="utf-8")
        assert not PLACEHOLDER_PATTERN.search(text), (
            f"unresolved placeholder in {path.relative_to(dest)}"
        )


# 15. Ausencia de secretos: no hay archivos con extensiones sensibles ni
# patrones literales de credenciales en el proyecto generado.
def test_no_secrets_in_generated_project(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    new_project.generate("My Project", "my_pkg", dest)
    for path in _list_files(dest):
        assert path.suffix.lower() not in SENSITIVE_SUFFIXES, (
            f"sensitive file extension: {path.relative_to(dest)}"
        )
    api_key_patterns = (
        re.compile(r"sk-[A-Za-z0-9]{20,}"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
    )
    for path in _list_files(dest):
        text = path.read_text(encoding="utf-8")
        for pattern in api_key_patterns:
            assert not pattern.search(text), (
                f"possible API key in {path.relative_to(dest)}"
            )


# 16. Ausencia de node_modules y otros artefactos runtime de OpenCode.
def test_no_opencode_runtime_artifacts(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    new_project.generate("My Project", "my_pkg", dest)
    opencode = dest / ".opencode"
    if opencode.is_dir():
        for entry in opencode.rglob("*"):
            if entry.is_file():
                assert entry.name not in FORBIDDEN_OPENCODE_NAMES, (
                    f"forbidden artifact: {entry.relative_to(dest)}"
                )


# 17. Un fallo durante la generación no deja destino parcial ni staging
# residual.
def test_failure_during_generation_leaves_no_partial_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "out"

    def failing_check(root: Path, package_name: str) -> list[str]:
        raise OSError("simulated validation failure")

    monkeypatch.setattr(new_project, "_check_required_paths", failing_check)

    rc = new_project.generate("My Project", "my_pkg", dest)
    assert rc != 0
    assert not dest.exists()
    for entry in tmp_path.iterdir():
        assert not entry.name.startswith(".new_project_"), (
            f"staging not cleaned: {entry}"
        )


# 18. Determinismo: dos generaciones con los mismos argumentos en destinos
# distintos producen el mismo conjunto de rutas y el mismo contenido.
def test_determinism_across_destinations(tmp_path: Path) -> None:
    dest1 = tmp_path / "first"
    dest2 = tmp_path / "second"
    assert new_project.generate("Determinism Test", "determinism_pkg", dest1) == 0
    assert new_project.generate("Determinism Test", "determinism_pkg", dest2) == 0
    snap1 = _snapshot(dest1)
    snap2 = _snapshot(dest2)
    assert snap1.keys() == snap2.keys()
    for key, content in snap1.items():
        assert content == snap2[key], f"content differs at {key}"


# 19. Los tests solo escriben dentro de tmp_path.
def test_tests_write_only_within_tmp_path(tmp_path: Path) -> None:
    before = {p.name for p in tmp_path.iterdir()}
    new_project.generate("A", "pkg_a", tmp_path / "a")
    new_project.generate("B", "pkg_b", tmp_path / "b")
    new_project.generate("C", "pkg_c", tmp_path / "c")
    after = {p.name for p in tmp_path.iterdir()}
    assert after == before | {"a", "b", "c"}


# 20. El proyecto generado contiene la estructura requerida.
def test_generated_project_has_required_structure(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    new_project.generate("My Project", "my_pkg", dest)
    required = [
        "pyproject.toml",
        "README.md",
        ".gitignore",
        "AGENTS.md",
        "opencode.jsonc",
        ".opencode",
        "docs",
        "src/my_pkg/__init__.py",
        "tests/test_smoke.py",
    ]
    for rel in required:
        assert (dest / rel).exists(), f"missing required path: {rel}"


# 21. Defecto E2E: con PROJECT_NAME con espacios y PACKAGE_NAME con
# underscores, [project].name usa el nombre de distribución derivado.
def test_e2e_smoke_uses_distribution_name(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    assert new_project.generate("E2E Smoke", "e2e_smoke", dest) == 0
    pyproject = (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "e2e-smoke"' in pyproject


# 22. El nombre visible se conserva en README y documentación.
def test_visible_name_preserved_in_readme_and_docs(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    new_project.generate("E2E Smoke", "e2e_smoke", dest)
    readme = (dest / "README.md").read_text(encoding="utf-8")
    assert "E2E Smoke" in readme
    init = (dest / "src" / "e2e_smoke" / "__init__.py").read_text(encoding="utf-8")
    assert "E2E Smoke package" in init
    smoke = (dest / "tests" / "test_smoke.py").read_text(encoding="utf-8")
    assert "E2E Smoke package" in smoke
    arch = (dest / "docs" / "architecture.md").read_text(encoding="utf-8")
    assert "E2E Smoke" in arch


# 23. El paquete sigue estando bajo src/<PACKAGE_NAME>/.
def test_package_layout_uses_package_name(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    new_project.generate("E2E Smoke", "e2e_smoke", dest)
    assert (dest / "src" / "e2e_smoke" / "__init__.py").is_file()
    pyproject = (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert 'packages = ["src/e2e_smoke"]' in pyproject


# 24. No queda ningún placeholder sin resolver, incluyendo
# {{DISTRIBUTION_NAME}}.
def test_no_unresolved_placeholders_including_distribution(
    tmp_path: Path,
) -> None:
    dest = tmp_path / "out"
    new_project.generate("E2E Smoke", "e2e_smoke", dest)
    forbidden = {
        "{{PROJECT_NAME}}",
        "{{PACKAGE_NAME}}",
        "{{DISTRIBUTION_NAME}}",
    }
    for path in _list_files(dest):
        text = path.read_text(encoding="utf-8")
        for placeholder in forbidden:
            assert placeholder not in text, (
                f"{placeholder} sin resolver en {path.relative_to(dest)}"
            )


# 25. El pyproject.toml generado es TOML válido y se puede leer con tomllib.
def test_pyproject_is_valid_toml(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    new_project.generate("E2E Smoke", "e2e_smoke", dest)
    data = tomllib.loads((dest / "pyproject.toml").read_text(encoding="utf-8"))
    assert "project" in data
    assert data["project"]["name"] == "e2e-smoke"


# 26. El nombre de distribución cumple el patrón PEP 503 / 508.
def test_distribution_name_matches_pep_pattern(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    new_project.generate("E2E Smoke", "e2e_smoke", dest)
    data = tomllib.loads((dest / "pyproject.toml").read_text(encoding="utf-8"))
    name = data["project"]["name"]
    assert re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", name), (
        f"{name!r} no cumple el patrón de nombre de distribución"
    )


# 27. Packages con caracteres no ASCII se rechazan antes de escribir.
def test_non_ascii_package_rejected(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    rc = new_project.generate("Café", "café", dest)
    assert rc != 0
    assert not dest.exists()
    for entry in tmp_path.iterdir():
        assert not entry.name.startswith(".new_project_"), (
            f"staging no limpiado: {entry}"
        )


# 28. Un fallo de validación no deja ni destino ni staging parcial.
def test_distribution_validation_failure_leaves_no_partial_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "out"

    def failing_distribution(package_name: str) -> str:
        raise OSError("simulated distribution derivation failure")

    monkeypatch.setattr(new_project, "_derive_distribution_name", failing_distribution)
    rc = new_project.generate("My Project", "my_pkg", dest)
    assert rc != 0
    assert not dest.exists()
    for entry in tmp_path.iterdir():
        assert not entry.name.startswith(".new_project_"), (
            f"staging no limpiado: {entry}"
        )
