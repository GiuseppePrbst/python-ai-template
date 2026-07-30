"""Tests del scanner read-only del audit.

Construye cada fixture con ``tmp_path`` y no depende del cwd ni del
repositorio real. Verifica:

    - Descubrimiento y lectura de ``.github/workflows/*.yml``.
    - Omision de directorios ocultos no autorizados.
    - No seguimiento de symlinks.
    - Las dos evidencias requeridas para el conflicto de version Python
      entre ``pyproject.toml`` y CI.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from python_ai_template.audit.scanner import scan  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_repo_with_ci_conflict(tmp_path: Path) -> Path:
    pyproject_content = (
        '[build-system]\nrequires = ["hatchling"]\n'
        'build-backend = "hatchling.build"\n\n'
        '[project]\nname = "x"\nversion = "0.1.0"\n'
        'requires-python = ">=3.12"\n'
    )
    _write(tmp_path / "pyproject.toml", pyproject_content)
    _write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        "name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        "    steps:\n      - uses: actions/setup-python@v5\n"
        '        with:\n          python-version: "3.11"\n',
    )
    return tmp_path


# 1. .github/workflows/ci.yml es descubierto y leido.
def test_discovers_github_workflows(tmp_path: Path) -> None:
    repo = _build_repo_with_ci_conflict(tmp_path)
    scanned = scan(repo)
    assert ".github/workflows/ci.yml" in scanned.ci_files_read
    assert "3.11" in scanned.ci_python_versions
    assert scanned.ci_files_read[".github/workflows/ci.yml"].startswith("name: CI")


# 2. Directorio oculto no autorizado se omite sin generar findings ni unknowns.
def test_unauthorized_hidden_dir_omitted(tmp_path: Path) -> None:
    _write(tmp_path / "pyproject.toml", '[project]\nname = "x"\n')
    _write(tmp_path / ".private" / "secret.txt", "should not be read")
    _write(tmp_path / ".private" / "inner" / "deeper.txt", "also hidden")
    scanned = scan(tmp_path)
    assert all(not k.startswith(".private") for k in scanned.allowlisted_docs_read)
    assert all(not k.startswith(".private") for k in scanned.allowlisted_config_read)
    assert ".private" not in scanned.symlinks


# 3. Los symlinks no se siguen y se registran.
def test_symlinks_not_followed(tmp_path: Path) -> None:
    _write(tmp_path / "pyproject.toml", '[project]\nname = "x"\n')
    real = tmp_path / "real.txt"
    real.write_text("real content", encoding="utf-8")
    link = tmp_path / "linked.txt"
    try:
        link.symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("el sistema no permite crear symlinks")
    scanned = scan(tmp_path)
    assert "linked.txt" in scanned.symlinks
    assert all(not k.endswith("linked.txt") for k in scanned.allowlisted_docs_read)


# 4. El conflicto entre pyproject.toml y CI recibe ambas evidencias.
def test_conflict_evidences_present(tmp_path: Path) -> None:
    repo = _build_repo_with_ci_conflict(tmp_path)
    scanned = scan(repo)
    assert scanned.pyproject_content is not None
    assert "requires-python" in scanned.pyproject_content
    assert ">=3.12" in scanned.pyproject_content
    assert ".github/workflows/ci.yml" in scanned.ci_files_read
    assert "3.11" in scanned.ci_python_versions


# 5. No se cuentan notebooks que viven bajo directorios ocultos no autorizados.
def test_notebooks_in_unauthorized_hidden_dir_not_counted(tmp_path: Path) -> None:
    _write(tmp_path / "pyproject.toml", '[project]\nname = "x"\n')
    _write(tmp_path / ".private" / "demo.ipynb", "{}")
    _write(tmp_path / "notebooks" / "01_ingesta.ipynb", "{}")
    scanned = scan(tmp_path)
    assert scanned.notebooks_operational == 1
    assert scanned.notebooks_total == 1


# 6. .fabric/ se omite silenciosamente; fabric/ no se excluye genericamente.
def test_dot_fabric_omitted_but_fabric_traversed(tmp_path: Path) -> None:
    _write(tmp_path / "pyproject.toml", '[project]\nname = "x"\n')
    _write(tmp_path / ".fabric" / "config.json", "irrelevant")
    _write(tmp_path / "fabric" / "config.json", "irrelevant")
    scanned = scan(tmp_path)
    keys = list(scanned.allowlisted_config_read) + list(scanned.allowlisted_docs_read)
    assert not any(k.startswith(".fabric") for k in keys)
    # pyproject + fabric/config (.fabric/ se omite silenciosamente)
    assert scanned.files_seen >= 2


# 7. No se ejecuta nada del target salvo los cuatro comandos Git allowlisted.
def test_no_target_files_executed(tmp_path: Path) -> None:
    _write(tmp_path / "pyproject.toml", '[project]\nname = "x"\n')
    _write(tmp_path / "scripts" / "run.py", "raise SystemExit(99)\n")
    scanned = scan(tmp_path)
    assert scanned.files_seen > 0
    assert scanned.operational_python_count >= 1
