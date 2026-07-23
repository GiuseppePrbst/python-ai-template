#!/usr/bin/env python3
"""Generador de proyectos Python a partir de la plantilla ``python-ai-template``.

Uso::

    python tools/new_project.py --name <nombre> --package <paquete> --destination <ruta>

El generador distingue tres conceptos:

- ``PROJECT_NAME``: nombre visible del proyecto. Puede contener espacios.
- ``PACKAGE_NAME``: nombre importable del paquete Python. Identificador
  válido, no keyword, solo ASCII.
- ``DISTRIBUTION_NAME``: nombre de distribución derivado de
  ``PACKAGE_NAME`` reemplazando ``_`` por ``-`` y convirtiendo a
  minúsculas. Se usa en ``[project].name`` de ``pyproject.toml``.

El generador valida los argumentos, deriva el nombre de distribución,
genera el árbol de archivos a partir de ``template/`` en un directorio de
staging temporal dentro del mismo padre que el destino, valida el
resultado y solo entonces lo mueve al destino final.

No ejecuta herramientas externas (``uv``, ``git``, ``subprocess``,
``shell``). No sobrescribe contenido existente. No copia secretos ni
artefactos de instalación local de OpenCode.
"""

from __future__ import annotations

import argparse
import keyword
import re
import shutil
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "template"

PROJECT_PLACEHOLDER = "{{PROJECT_NAME}}"
PACKAGE_PLACEHOLDER = "{{PACKAGE_NAME}}"
DISTRIBUTION_NAME_PLACEHOLDER = "{{DISTRIBUTION_NAME}}"
PLACEHOLDER_PATTERN = re.compile(r"\{\{[^}]*\}\}")
DISTRIBUTION_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

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

PACKAGE_DIR_PLACEHOLDER = "__package_name__"
TEMPLATE_SUFFIX = ".tmpl"

REQUIRED_RELATIVE_PATHS: tuple[str, ...] = (
    "pyproject.toml",
    "README.md",
    ".gitignore",
    "AGENTS.md",
    "opencode.jsonc",
    ".opencode",
    "docs",
    "tests/test_smoke.py",
)


def _error(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)


def _validate_name(name: str) -> str | None:
    if not name:
        return "el nombre del proyecto no puede estar vacío"
    if not name.strip():
        return "el nombre del proyecto no puede estar compuesto solo por espacios"
    return None


def _validate_package(package: str) -> str | None:
    if not package:
        return "el nombre del paquete no puede estar vacío"
    if not package.strip():
        return "el nombre del paquete no puede estar compuesto solo por espacios"
    if not package.isidentifier():
        return (
            "el nombre del paquete debe ser un identificador Python válido: "
            f"{package!r}"
        )
    if keyword.iskeyword(package):
        return f"el nombre del paquete no puede ser una keyword de Python: {package!r}"
    if not package.isascii():
        return f"el nombre del paquete debe contener solo caracteres ASCII: {package!r}"
    for ch in (".", "-", " ", "/", "\\"):
        if ch in package:
            return (
                "el nombre del paquete no puede contener el carácter "
                f"{ch!r}: {package!r}"
            )
    return None


def _derive_distribution_name(package_name: str) -> str:
    return package_name.lower().replace("_", "-")


def _render(
    text: str, project_name: str, package_name: str, distribution_name: str
) -> str:
    return (
        text.replace(PROJECT_PLACEHOLDER, project_name)
        .replace(PACKAGE_PLACEHOLDER, package_name)
        .replace(DISTRIBUTION_NAME_PLACEHOLDER, distribution_name)
    )


def _compute_dest_path(rel: Path, package_name: str, *, is_dir: bool) -> Path:
    parts = [
        package_name if part == PACKAGE_DIR_PLACEHOLDER else part for part in rel.parts
    ]
    if not is_dir and parts[-1].endswith(TEMPLATE_SUFFIX):
        parts[-1] = parts[-1][: -len(TEMPLATE_SUFFIX)]
    return Path(*parts)


def _check_unresolved_placeholders(root: Path) -> list[Path]:
    offenders: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if PLACEHOLDER_PATTERN.search(path.read_text(encoding="utf-8")):
            offenders.append(path)
    return offenders


def _check_forbidden_opencode_artifacts(root: Path) -> list[Path]:
    offenders: list[Path] = []
    opencode = root / ".opencode"
    if not opencode.is_dir():
        return offenders
    for path in sorted(opencode.rglob("*")):
        if path.is_file() and path.name in FORBIDDEN_OPENCODE_NAMES:
            offenders.append(path)
    return offenders


def _check_sensitive_files(root: Path) -> list[Path]:
    offenders: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SENSITIVE_SUFFIXES:
            offenders.append(path)
    return offenders


def _check_required_paths(root: Path, package_name: str) -> list[str]:
    required = [*REQUIRED_RELATIVE_PATHS, f"src/{package_name}/__init__.py"]
    return [p for p in required if not (root / p).exists()]


def generate(project_name: str, package_name: str, destination: Path) -> int:
    if (err := _validate_name(project_name)) is not None:
        _error(err)
        return 2
    if (err := _validate_package(package_name)) is not None:
        _error(err)
        return 2

    try:
        distribution_name = _derive_distribution_name(package_name)
    except Exception as exc:  # noqa: BLE001
        _error(f"no se pudo derivar el nombre de distribución: {exc}")
        return 1
    if not DISTRIBUTION_NAME_PATTERN.match(distribution_name):
        _error(
            f"el nombre de distribución derivado {distribution_name!r} no "
            f"cumple el patrón ^[a-z0-9]+(?:-[a-z0-9]+)*$ a partir de "
            f"{package_name!r}"
        )
        return 2

    dest_abs = destination if destination.is_absolute() else destination.resolve()
    parent = dest_abs.parent

    if dest_abs.exists():
        _error(
            f"el destino {dest_abs} ya existe; no se sobrescribe ni se mezcla "
            f"con contenido existente"
        )
        return 2

    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        _error(f"no se pudo crear o acceder a la ruta padre {parent}: {exc}")
        return 1
    if not parent.is_dir():
        _error(f"la ruta padre {parent} existe y no es un directorio")
        return 1

    try:
        staging = Path(tempfile.mkdtemp(prefix=".new_project_", dir=parent))
    except OSError as exc:
        _error(f"no se pudo crear el directorio temporal de staging: {exc}")
        return 1

    cleanup_staging = True
    try:
        for src in sorted(TEMPLATE_DIR.rglob("*")):
            is_dir = src.is_dir()
            rel = src.relative_to(TEMPLATE_DIR)
            dest_rel = _compute_dest_path(rel, package_name, is_dir=is_dir)
            dest_path = staging / dest_rel
            if is_dir:
                dest_path.mkdir(parents=True, exist_ok=True)
                continue
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            content = src.read_text(encoding="utf-8")
            rendered = _render(content, project_name, package_name, distribution_name)
            dest_path.write_text(rendered, encoding="utf-8", newline="\n")

        offenders = _check_unresolved_placeholders(staging)
        if offenders:
            for path in offenders:
                _error(f"placeholder sin resolver en {path.relative_to(staging)}")
            return 3

        offenders = _check_forbidden_opencode_artifacts(staging)
        if offenders:
            for path in offenders:
                _error(
                    f"artefacto de OpenCode no permitido: {path.relative_to(staging)}"
                )
            return 4

        offenders = _check_sensitive_files(staging)
        if offenders:
            for path in offenders:
                _error(
                    "archivo potencialmente sensible detectado: "
                    f"{path.relative_to(staging)}"
                )
            return 6

        missing = _check_required_paths(staging, package_name)
        if missing:
            for p in missing:
                _error(f"falta el archivo o directorio obligatorio: {p}")
            return 5

        if dest_abs.exists():
            _error(
                f"el destino {dest_abs} apareció durante la generación; "
                f"se cancela para no sobrescribir"
            )
            return 1

        try:
            staging.rename(dest_abs)
        except OSError as exc:
            _error(f"no se pudo mover el staging al destino final: {exc}")
            return 7
        cleanup_staging = False
    except Exception as exc:  # noqa: BLE001
        _error(f"error durante la generación: {exc}")
        return 1
    finally:
        if cleanup_staging and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    print(f"Proyecto generado en {dest_abs}")
    print(f"Nombre de distribución: {distribution_name}")
    print("Próximos pasos:")
    print(f"  cd {dest_abs}")
    print("  uv sync")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="new_project",
        description=(
            "Genera un proyecto Python a partir de la plantilla python-ai-template."
        ),
    )
    parser.add_argument("--name", required=True, help="nombre visible del proyecto")
    parser.add_argument(
        "--package",
        required=True,
        help=(
            "nombre del paquete Python (identificador válido, no keyword, "
            "solo ASCII, sin puntos, guiones, espacios ni separadores de "
            "ruta)"
        ),
    )
    parser.add_argument(
        "--destination",
        required=True,
        help="ruta del directorio destino (no debe existir)",
    )
    args = parser.parse_args(argv)
    return generate(args.name, args.package, Path(args.destination))


if __name__ == "__main__":
    sys.exit(main())
