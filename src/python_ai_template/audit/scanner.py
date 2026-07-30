"""Scanner read-only del repositorio auditado.

Reglas de oro:
    - No se escribe nada dentro del target.
    - Los symlinks se registran como ``suspicious-config`` y se omite su
      contenido.
    - Directorios canonicos (``SILENT_DIRS``) se omiten sin generar
      findings ni unknowns.
    - Solo se lee contenido de archivos en allowlist
      (``CONTENT_ALLOWLIST`` o rutas que coincidan con ``PATH_GLOB_ALLOWLIST``).
    - Los notebooks se cuentan sin abrirse jamas.
    - Solo se ejecutan los cuatro comandos Git allowlisted, con
      ``GIT_OPTIONAL_LOCKS=0`` y ``cwd`` en el target (el criterio de no
      ejecucion se limita a no correr codigo, scripts o binarios del
      target distintos de Git con allowlist cerrada).
    - La deteccion de integraciones se hace unicamente desde
      pyproject.toml, requirements, package.json, CI, configuracion,
      documentacion allowlisted, nombres de archivo o directorio y
      artefactos explicitos.
    - Las categorias de denylist acumulan conteos sin exponer nombres.
"""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

# Allowlist de archivos cuyo contenido puede leerse (sin path).
CONTENT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "AGENTS.md",
        "README.md",
        "README.rst",
        "README.txt",
        "README",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "requirements.in",
        "requirements-dev.txt",
        "requirements-lint.txt",
        "package.json",
        "ruff.toml",
        ".ruff.toml",
        "mypy.ini",
        ".mypy.ini",
        "pyrightconfig.json",
        ".pyrightconfig.json",
        ".pre-commit-config.yaml",
        ".gitlab-ci.yml",
        "azure-pipelines.yml",
        "Makefile",
        "Justfile",
    }
)

# Allowlist de rutas con glob para archivos cuyo contenido puede leerse.
PATH_GLOB_ALLOWLIST: tuple[str, ...] = (
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    "docs/decisions.md",
    "docs/adr/*.md",
    "docs/adr/*/index.md",
    "docs/architecture.md",
    "ARCHITECTURE.md",
    "docs/architecture/*.md",
    "docs/contracts/*.md",
    "docs/process*.md",
    "CONTRACT*",
    "CONTRACTS*",
    "PROCESO*",
)

# Directorios omitidos silenciosamente (sin findings, sin unknowns).
SILENT_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "dist",
        "build",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".pyright",
        ".fabric",
    }
)

# Directorios ocultos que aun asi se recorren (para CI workflows, etc.).
TRAVERSED_HIDDEN_DIRS: frozenset[str] = frozenset(
    {
        ".github",
        ".gitlab",
        ".config",
        ".devcontainer",
        ".vscode",
    }
)

# Patrones de denylist por categoria. Solo se acumula el contador.
DENYLIST_PATTERNS: dict[str, tuple[str, ...]] = {
    "secrets": (
        ".env",
        ".envrc",
        ".pem",
        ".key",
        ".pfx",
        ".p12",
        ".gpg",
        ".asc",
        "secrets.yaml",
        "secrets.yml",
        "secrets.json",
        "secrets.toml",
        "id_rsa",
        "id_ed25519",
        ".netrc",
        ".pgpass",
        ".pg_service.conf",
        ".git-credentials",
    ),
    "credentials": (
        "*credentials*",
        "*password*",
        "*apikey*",
        "*api_key*",
        "credentials.json",
    ),
    "data-binary": (
        "*.parquet",
        "*.arrow",
        "*.feather",
        "*.orc",
        "*.h5",
        "*.hdf5",
        "*.pkl",
        "*.pickle",
        "*.db",
        "*.sqlite",
        "*.sqlite3",
    ),
}

# Paths operativos por dominio.
NOTEBOOK_OPERATIONAL_PATHS: frozenset[str] = frozenset(
    {
        "notebooks",
        "pipelines",
        "jobs",
        "tasks",
        "dags",
        "flows",
        "orquestador",
    }
)
SQL_OPERATIONAL_PATHS: frozenset[str] = frozenset(
    {
        "migrations",
        "db",
        "sql",
        "schema",
    }
)
DATA_OPERATIONAL_PATHS: frozenset[str] = frozenset(
    {
        "data",
        "datasets",
        "raw",
        "processed",
    }
)
PIPELINE_DIR_NAMES: frozenset[str] = NOTEBOOK_OPERATIONAL_PATHS

# Paths cuyo contenido se considera de peso reducido (x0.25) para senales.
REDUCED_PATHS: frozenset[str] = frozenset(
    {
        "examples",
        "samples",
        "docs",
    }
)
REDUCED_FIXTURE_PREFIX: tuple[str, ...] = ("tests", "fixtures")

# Directorios excluidos de deteccion de paquetes.
PACKAGE_DETECTION_EXCLUDED: frozenset[str] = frozenset(
    {
        "tests",
        "test",
        "docs",
        "examples",
        "samples",
        "scripts",
        "tools",
        "build",
        "dist",
    }
)

MAX_INSPECT_BYTES = 1 * 1024 * 1024
MAX_DATA_BYTES = 256 * 1024
MAX_DEPTH = 8
MAX_FILES = 50_000
GIT_TIMEOUT = 10


# Patrones para detectar integraciones desde fuentes allowlisted.
INTEGRATION_PATTERNS: dict[str, re.Pattern[str]] = {
    "fabric": re.compile(
        r"\b(fabric|notebookutils|onelake|sempy|spark|pyspark)\b",
        re.IGNORECASE,
    ),
    "azure": re.compile(
        r"\b(azure[_-]?(?:identity|storage|ml|keyvault)|msal)\b",
        re.IGNORECASE,
    ),
    "aws": re.compile(
        r"\b(boto3|aws[_-]?(?:s3|sdk|sso))\b",
        re.IGNORECASE,
    ),
    "gcp": re.compile(
        r"\b(google[_-]?(?:cloud|storage|bigquery)|gcp)\b",
        re.IGNORECASE,
    ),
}


@dataclass
class ScannedRepository:
    target: Path
    symlinks: list[str] = field(default_factory=list[str])
    files_seen: int = 0

    has_pyproject: bool = False
    pyproject_content: str | None = None
    has_setup_py: bool = False
    has_setup_cfg: bool = False

    requirements_files: list[str] = field(default_factory=list[str])

    src_layout_dirs: list[str] = field(default_factory=list[str])
    top_level_packages: list[str] = field(default_factory=list[str])

    scripts_dir: bool = False
    operational_python_count: int = 0
    examples_python_count: int = 0

    has_tests_dir: bool = False

    notebooks_total: int = 0
    notebooks_operational: int = 0
    notebooks_in_examples: int = 0

    sql_total: int = 0
    sql_operational: int = 0

    data_dirs: list[str] = field(default_factory=list[str])
    pipeline_dirs: list[str] = field(default_factory=list[str])

    ci_workflows: list[str] = field(default_factory=list[str])
    ci_python_versions: list[str] = field(default_factory=list[str])
    ci_files_read: dict[str, str] = field(default_factory=dict[str, str])

    allowlisted_docs_read: dict[str, str] = field(default_factory=dict[str, str])
    allowlisted_config_read: dict[str, str] = field(default_factory=dict[str, str])

    integrations_evidence: dict[str, list[str]] = field(
        default_factory=dict[str, list[str]]
    )
    denylist_counts: dict[str, int] = field(default_factory=dict[str, int])

    git_info: dict[str, Any] | None = None
    truncated: bool = False
    git_unavailable: bool = False


def _match_any(name: str, patterns: Iterable[str]) -> bool:
    for p in patterns:
        if fnmatch(name, p):
            return True
    return False


def _is_in_reduced_path(rel_parts: tuple[str, ...]) -> bool:
    """Indica si un archivo esta bajo examples/samples/docs o tests/fixtures."""
    if not rel_parts:
        return False
    if rel_parts[0] in REDUCED_PATHS:
        return True
    if (
        len(rel_parts) >= 2
        and rel_parts[0] == REDUCED_FIXTURE_PREFIX[0]
        and rel_parts[1] == REDUCED_FIXTURE_PREFIX[1]
    ):
        return True
    return False


def _read_text(path: Path) -> str | None:
    try:
        st = path.stat()
    except OSError:
        return None
    if st.st_size > MAX_INSPECT_BYTES:
        return None
    try:
        with path.open("rb") as f:
            data = f.read()
    except OSError:
        return None
    return data.decode("utf-8", errors="replace")


def _detect_ci_python_versions(content: str) -> list[str]:
    matches: list[str] = []
    pattern = re.compile(r"python-version:\s*[\"']?([0-9.]+)[\"']?")
    for line in content.splitlines():
        m = pattern.search(line)
        if m:
            matches.append(m.group(1))
    return matches


def _detect_integrations_from_text(text: str, source: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for name, pattern in INTEGRATION_PATTERNS.items():
        if pattern.search(text):
            found.setdefault(name, []).append(source)
    return found


def _process_file(
    entry: Path,
    rel_parts: tuple[str, ...],
    rel_str: str,
    repo: ScannedRepository,
) -> None:
    name = entry.name

    # Denylist por categoria: acumula contador y no inspecciona contenido.
    for category, patterns in DENYLIST_PATTERNS.items():
        if _match_any(name, patterns):
            repo.denylist_counts[category] = repo.denylist_counts.get(category, 0) + 1
            return
    if _match_any(name, ("*.csv", "*.tsv")):
        try:
            if entry.stat().st_size > MAX_DATA_BYTES:
                repo.denylist_counts["data-tabular-large"] = (
                    repo.denylist_counts.get("data-tabular-large", 0) + 1
                )
                return
        except OSError:
            return

    # Deteccion de paquetes: __init__.py en posiciones validas.
    if name == "__init__.py":
        if len(rel_parts) >= 3 and rel_parts[0] == "src":
            pkg_name = rel_parts[1]
            if (
                pkg_name not in PACKAGE_DETECTION_EXCLUDED
                and not pkg_name.startswith(".")
                and pkg_name not in repo.src_layout_dirs
            ):
                repo.src_layout_dirs.append(pkg_name)
            return
        if len(rel_parts) == 2:
            pkg_name = rel_parts[0]
            if (
                pkg_name not in PACKAGE_DETECTION_EXCLUDED
                and not pkg_name.startswith(".")
                and pkg_name not in repo.top_level_packages
            ):
                repo.top_level_packages.append(pkg_name)
            return
        return

    # Notebooks: contar, nunca abrir.
    if name.endswith(".ipynb"):
        repo.notebooks_total += 1
        if len(rel_parts) >= 2 and rel_parts[0] in NOTEBOOK_OPERATIONAL_PATHS:
            repo.notebooks_operational += 1
        elif _is_in_reduced_path(rel_parts):
            repo.notebooks_in_examples += 1
        return

    # SQL: contar y clasificar.
    if name.endswith(".sql"):
        repo.sql_total += 1
        if len(rel_parts) >= 2 and rel_parts[0] in SQL_OPERATIONAL_PATHS:
            repo.sql_operational += 1
        elif _is_in_reduced_path(rel_parts):
            pass
        return

    # Scripts Python operativos fuera de paquetes y fuera de rutas reducidas.
    if name.endswith(".py"):
        top = rel_parts[0] if rel_parts else ""
        if _is_in_reduced_path(rel_parts):
            repo.examples_python_count += 1
        elif top == "src" and len(rel_parts) >= 2:
            return
        elif top not in SILENT_DIRS and not top.startswith("."):
            repo.operational_python_count += 1
        return

    # Archivos de configuracion y documentacion allowlisted.
    if name in CONTENT_ALLOWLIST:
        text = _read_text(entry)
        if text is None:
            return
        if name == "pyproject.toml":
            repo.has_pyproject = True
            repo.pyproject_content = text
            repo.allowlisted_config_read[rel_str] = text
        elif name == "setup.py":
            repo.has_setup_py = True
            repo.allowlisted_config_read[rel_str] = text
        elif name == "setup.cfg":
            repo.has_setup_cfg = True
            repo.allowlisted_config_read[rel_str] = text
        elif _match_any(name, ("requirements*.txt", "requirements*.in")):
            repo.requirements_files.append(rel_str)
            repo.allowlisted_config_read[rel_str] = text
        else:
            repo.allowlisted_docs_read[rel_str] = text
        for int_name, sources in _detect_integrations_from_text(text, rel_str).items():
            for src in sources:
                repo.integrations_evidence.setdefault(int_name, []).append(src)
        return

    # Glob allowlist (CI workflows y documentacion por path).
    for pattern in PATH_GLOB_ALLOWLIST:
        if fnmatch(rel_str, pattern):
            text = _read_text(entry)
            if text is None:
                return
            if pattern.startswith(".github/workflows/"):
                if rel_str not in repo.ci_workflows:
                    repo.ci_workflows.append(rel_str)
                repo.ci_files_read[rel_str] = text
                for ver in _detect_ci_python_versions(text):
                    if ver not in repo.ci_python_versions:
                        repo.ci_python_versions.append(ver)
            else:
                repo.allowlisted_docs_read[rel_str] = text
            detected = _detect_integrations_from_text(text, rel_str)
            for int_name, sources in detected.items():
                for src in sources:
                    repo.integrations_evidence.setdefault(int_name, []).append(src)
            return


def _scan_dir(
    target: Path,
    directory: Path,
    depth: int,
    repo: ScannedRepository,
) -> None:
    if depth > MAX_DEPTH:
        repo.truncated = True
        return
    try:
        entries = list(directory.iterdir())
    except (OSError, PermissionError):
        return
    for entry in entries:
        if entry.is_symlink():
            try:
                rel = entry.relative_to(target)
            except ValueError:
                rel = Path(entry.name)
            repo.symlinks.append(str(rel))
            continue
        try:
            rel_parts = entry.relative_to(target).parts
        except ValueError:
            rel_parts = (entry.name,)
        if entry.is_dir():
            if entry.name in SILENT_DIRS:
                continue
            top_hidden = rel_parts[0].startswith(".") if rel_parts else False
            if top_hidden and rel_parts[0] not in TRAVERSED_HIDDEN_DIRS:
                continue
            if entry.name in ("tests", "test"):
                repo.has_tests_dir = True
            if entry.name in PIPELINE_DIR_NAMES:
                if entry.name not in repo.pipeline_dirs:
                    repo.pipeline_dirs.append(entry.name)
            if entry.name in DATA_OPERATIONAL_PATHS:
                if entry.name not in repo.data_dirs:
                    repo.data_dirs.append(entry.name)
            if entry.name == "scripts":
                repo.scripts_dir = True
            if depth + 1 <= MAX_DEPTH:
                _scan_dir(target, entry, depth + 1, repo)
            continue
        if not entry.is_file():
            continue
        top_hidden = rel_parts[0].startswith(".") if rel_parts else False
        if top_hidden and rel_parts[0] not in TRAVERSED_HIDDEN_DIRS:
            continue
        if repo.files_seen >= MAX_FILES:
            repo.truncated = True
            return
        rel_str = str(entry.relative_to(target))
        repo.files_seen += 1
        _process_file(entry, rel_parts, rel_str, repo)


def _read_git_info(target: Path) -> dict[str, Any] | None:
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    info: dict[str, Any] = {}
    try:
        probe = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=target,
            shell=False,
            env=env,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if probe.returncode != 0:
        return None
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=target,
            shell=False,
            env=env,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
        )
        if head.returncode == 0:
            value = head.stdout.strip()
            if value:
                info["head"] = value
    except (OSError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=target,
            shell=False,
            env=env,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
        )
        if branch.returncode == 0:
            value = branch.stdout.strip()
            if value:
                info["branch"] = value
    except (OSError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    try:
        status = subprocess.run(
            ["git", "status", "--short", "--porcelain"],
            cwd=target,
            shell=False,
            env=env,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
        )
        if status.returncode == 0:
            lines = [ln for ln in status.stdout.splitlines() if ln]
            info["porcelain_clean"] = len(lines) == 0
            info["untracked_count"] = sum(1 for ln in lines if ln.startswith("??"))
            info["modified_count"] = sum(
                1 for ln in lines if ln and not ln.startswith("??")
            )
    except (OSError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return info if info else None


def scan(target: Path) -> ScannedRepository:
    """Recorre el repositorio y devuelve las senales detectadas."""
    repo = ScannedRepository(target=target)
    _scan_dir(target, target, 0, repo)
    git_dir = target / ".git"
    if git_dir.is_dir():
        info = _read_git_info(target)
        if info is None:
            repo.git_unavailable = True
        else:
            repo.git_info = info
    else:
        repo.git_unavailable = True
    return repo
