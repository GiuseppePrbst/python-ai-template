"""Nucleo del generador de proyectos Python.

El modulo expone la funcion :func:`generate` y los helpers que implementan la
sustitucion de placeholders, la validacion semantica del arbol generado y la
politica de staging. La plantilla se obtiene en tiempo de ejecucion como
recurso del paquete (``importlib.resources``), por lo que el modulo no depende
de la ruta del repositorio ni del directorio de trabajo.

El comportamiento publico (firmas, codigos de salida, conjunto de
validaciones) coincide con la version previa del generador. La
reorganizacion interna afecta solo a como se descubre la plantilla: en
lugar de una ruta en disco se usa un ``Traversable`` que se recorre en
orden determinista, conservando nombres como ``.gitignore``, ``.opencode``
y ``__package_name__``.
"""

from __future__ import annotations

import importlib.resources
import keyword
import re
import shutil
import sys
import tempfile
from collections.abc import Iterator, Sequence
from importlib.resources.abc import Traversable
from pathlib import Path

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
        return "el nombre del proyecto no puede estar vacio"
    if not name.strip():
        return "el nombre del proyecto no puede estar compuesto solo por espacios"
    return None


def _validate_package(package: str) -> str | None:
    if not package:
        return "el nombre del paquete no puede estar vacio"
    if not package.strip():
        return "el nombre del paquete no puede estar compuesto solo por espacios"
    if not package.isidentifier():
        return (
            "el nombre del paquete debe ser un identificador Python valido: "
            f"{package!r}"
        )
    if keyword.iskeyword(package):
        return f"el nombre del paquete no puede ser una keyword de Python: {package!r}"
    if not package.isascii():
        return f"el nombre del paquete debe contener solo caracteres ASCII: {package!r}"
    for ch in (".", "-", " ", "/", "\\"):
        if ch in package:
            return (
                "el nombre del paquete no puede contener el caracter "
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


def _walk_template(
    root: Traversable,
) -> Iterator[tuple[Path, Traversable]]:
    """Recorre recursivamente un ``Traversable`` y emite cada archivo.

    La iteracion es determinista: las entradas de cada directorio se
    ordenan por nombre. Se conservan literalmente nombres especiales
    como ``.gitignore``, ``.opencode``, ``__package_name__`` y archivos
    ``.tmpl``. Solo se emiten archivos; los directorios se crean a
    partir de las rutas relativas.
    """

    def _walk(
        directory: Traversable, prefix: Path
    ) -> Iterator[tuple[Path, Traversable]]:
        for entry in sorted(directory.iterdir(), key=lambda e: e.name):
            entry_path = prefix / entry.name
            if entry.is_dir():
                yield from _walk(entry, entry_path)
            else:
                yield entry_path, entry

    yield from _walk(root, Path())


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


def _template_root() -> Traversable:
    """Devuelve la raiz de la plantilla como ``Traversable``.

    La plantilla viaja como ``package data`` dentro del paquete
    ``python_ai_template``. ``importlib.resources.files`` resuelve al
    ``Traversable`` raiz del paquete sin depender del directorio de
    trabajo ni de la ruta del repositorio; ``joinpath("template")``
    apunta al subdirectorio parametrizado. Funciona en instalacion
    normal (``uv tool install``), en instalacion editable y en
    zip-install.
    """
    return importlib.resources.files("python_ai_template").joinpath("template")


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
        _error(f"no se pudo derivar el nombre de distribucion: {exc}")
        return 1
    if not DISTRIBUTION_NAME_PATTERN.match(distribution_name):
        _error(
            f"el nombre de distribucion derivado {distribution_name!r} no "
            f"cumple el patron ^[a-z0-9]+(?:-[a-z0-9]+)*$ a partir de "
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
        try:
            template_files = list(_walk_template(_template_root()))
        except (FileNotFoundError, OSError) as exc:
            _error(f"no se pudo acceder a la plantilla del paquete: {exc}")
            return 1

        for rel, entry in template_files:
            dest_rel = _compute_dest_path(rel, package_name, is_dir=False)
            dest_path = staging / dest_rel
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            content = entry.read_text(encoding="utf-8")
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
                f"el destino {dest_abs} aparecio durante la generacion; "
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
        _error(f"error durante la generacion: {exc}")
        return 1
    finally:
        if cleanup_staging and staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    print(f"Proyecto generado en {dest_abs}")
    print(f"Nombre de distribucion: {distribution_name}")
    print("Proximos pasos:")
    print(f"  cd {dest_abs}")
    print("  uv sync")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada opcional para ``python -m python_ai_template.generator``."""
    from python_ai_template.cli import main as cli_main

    return cli_main(argv)


if __name__ == "__main__":
    sys.exit(main())
