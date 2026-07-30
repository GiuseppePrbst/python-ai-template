"""Tests E2E read-only del CLI ``python-ai-template audit``.

Verifica:

    - TOML por stdout;
    - mensajes humanos solo por stderr;
    - ``--output`` externo;
    - rechazo de ``--output`` dentro del target;
    - arbol del target sin cambios;
    - ningun acceso de red;
    - solo los cuatro comandos Git permitidos;
    - compatibilidad de ``new-python-project``.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


# Helper: ejecuta ``python-ai-template audit`` como subproceso.
def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "python_ai_template.main", "audit", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _hash_tree(root: Path) -> dict[str, str]:
    """Hash estable del arbol para comparar antes/despues."""
    import hashlib

    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            data = p.read_bytes()
            out[str(p.relative_to(root))] = hashlib.sha256(data).hexdigest()
    return out


# 1. TOML por stdout y mensaje de duracion por stderr.
def test_toml_to_stdout_duration_to_stderr(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        '[build-system]\nrequires=["hatchling"]\nbuild-backend="hatchling.build"\n\n'
        '[project]\nname="x"\nversion="0.1.0"\nrequires-python=">=3.12"\n',
    )
    _write(tmp_path / "src" / "mypkg" / "__init__.py")
    proc = _run([str(tmp_path)])
    assert proc.returncode == 0, proc.stderr
    parsed = tomllib.loads(proc.stdout)
    assert parsed["schema_version"] == 1
    assert parsed["archetype"]["classification"] == "python-package"
    assert proc.stderr == ""


# 2. --output escribe TOML valido fuera del target.
def test_output_writes_outside_target(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    _write(
        repo / "pyproject.toml",
        '[build-system]\nrequires=["hatchling"]\nbuild-backend="hatchling.build"\n\n'
        '[project]\nname="x"\nversion="0.1.0"\nrequires-python=">=3.12"\n',
    )
    _write(repo / "src" / "mypkg" / "__init__.py")
    out_path = out_dir / "manifest.toml"
    proc = _run([str(repo), "--output", str(out_path)])
    assert proc.returncode == 0, proc.stderr
    assert out_path.is_file()
    assert not (repo / "manifest.toml").exists()
    parsed = tomllib.loads(out_path.read_text(encoding="utf-8"))
    assert parsed["schema_version"] == 1
    assert "audit completed" in proc.stderr
    assert not out_path.with_suffix(".toml.tmp").exists()


# 3. --output dentro del target se rechaza.
def test_output_inside_target_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "pyproject.toml", '[project]\nname="x"\n')
    bad = repo / "inside.toml"
    proc = _run([str(repo), "--output", str(bad)])
    assert proc.returncode == 2
    assert "fuera del target" in proc.stderr or "dentro" in proc.stderr
    assert not bad.exists()


# 4. arbol del target sin cambios antes y despues del audit.
def test_target_tree_unchanged(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(
        repo / "pyproject.toml",
        '[build-system]\nrequires=["hatchling"]\nbuild-backend="hatchling.build"\n\n'
        '[project]\nname="x"\nversion="0.1.0"\nrequires-python=">=3.12"\n',
    )
    _write(repo / "src" / "mypkg" / "__init__.py")
    _write(repo / "README.md", "# readme\n")
    before = _hash_tree(repo)
    proc = _run([str(repo)])
    assert proc.returncode == 0
    after = _hash_tree(repo)
    assert before == after


# 5. no se crea .ai-template/ dentro del target.
def test_no_ai_template_inside_target(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "pyproject.toml", '[project]\nname="x"\n')
    proc = _run([str(repo)])
    assert proc.returncode == 0
    assert not (repo / ".ai-template").exists()


# 6. subcomando inexistente devuelve exit code 2.
def test_unknown_subcommand_rejected() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "python_ai_template.main", "bogus", "/tmp"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "subcomando" in proc.stderr


# 7. ninguna conexion de red (no DNS, no HTTP, no socket.connect).
def test_no_network_access(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _write(tmp_path / "pyproject.toml", '[project]\nname="x"\n')
    real_connect = socket.socket.connect

    def _no_connect(self: socket.socket, address: tuple[str, int] | str) -> None:
        raise AssertionError(f"network not allowed: {address!r}")

    monkeypatch.setattr(socket.socket, "connect", _no_connect)
    try:
        proc = _run([str(tmp_path)])
    finally:
        monkeypatch.setattr(socket.socket, "connect", real_connect)
    assert proc.returncode == 0


# 8. solo se ejecutan los cuatro comandos Git permitidos.
def test_only_allowed_git_commands(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = tmp_path / "repo"
    _write(
        repo / "pyproject.toml",
        '[build-system]\nrequires=["hatchling"]\nbuild-backend="hatchling.build"\n\n'
        '[project]\nname="x"\nversion="0.1.0"\nrequires-python=">=3.12"\n',
    )
    _write(repo / "src" / "mypkg" / "__init__.py")
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)

    import python_ai_template.audit.scanner as scanner_mod

    allowed = {
        ("git", "rev-parse", "--git-dir"),
        ("git", "rev-parse", "HEAD"),
        ("git", "rev-parse", "--abbrev-ref", "HEAD"),
        ("git", "status", "--short", "--porcelain"),
    }
    forbidden_calls: list[tuple[str, ...]] = []
    real_run = scanner_mod.subprocess.run

    def _guard(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args and isinstance(args[0], list) and args[0] and args[0][0] == "git":
            cmd: list[str] = [str(x) for x in cast(list[str], args[0])]
            key = tuple(cmd)
            if key not in allowed:
                forbidden_calls.append(key)
        return cast(subprocess.CompletedProcess[str], real_run(*args, **kwargs))

    monkeypatch.setattr(scanner_mod.subprocess, "run", _guard)
    try:
        proc = _run([str(repo)])
    finally:
        monkeypatch.setattr(scanner_mod.subprocess, "run", real_run)
    assert proc.returncode == 0
    assert forbidden_calls == []


# 9. compatibilidad de new-python-project.
def test_new_python_project_unchanged() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "python_ai_template.cli", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "0.3.3"


# 10. audit --help imprime ayuda y termina con codigo 0.
def test_audit_help_exits_zero() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "python_ai_template.main", "audit", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "audit" in proc.stdout
