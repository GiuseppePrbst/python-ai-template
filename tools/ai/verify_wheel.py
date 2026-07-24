"""Verificador del wheel de ``python-ai-template``.

Comprueba que el wheel producido por ``uv build`` en ``dist/`` satisface las
siguientes propiedades y termina con codigo no cero ante cualquier discrepancia:

    1. ``pyproject.toml`` declara ``project.version`` como string.
    2. ``src/python_ai_template/__init__.py`` contiene exactamente una
       asignacion ``__version__ = "..."`` donde el valor es un string literal
       (extraccion estatica via ``ast``, sin importar ni ejecutar el modulo).
    3. Existe exactamente un ``*.whl`` en ``dist/``.
    4. El nombre del wheel comienza por ``python_ai_template-<version>-``.
    5. El wheel contiene exactamente un ``METADATA`` dentro de
       ``.dist-info`` y su campo ``Version`` coincide con las fuentes 1, 2 y 4.
    6. El wheel contiene todos los recursos obligatorios de la plantilla.

Las cuatro fuentes de la version que se contrastan entre si:

    - ``pyproject.toml``
    - ``__version__`` en ``__init__.py``
    - nombre del wheel
    - ``METADATA Version`` dentro del wheel

Usa solo biblioteca estandar: ``ast``, ``pathlib``, ``tomllib``, ``zipfile``
y, si son necesarios, ``sys`` y ``collections``.
"""

from __future__ import annotations

import ast
import sys
import tomllib
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
INIT_PATH = REPO_ROOT / "src" / "python_ai_template" / "__init__.py"
DIST_PATH = REPO_ROOT / "dist"

DISTRIBUTION_SLUG = "python_ai_template"

REQUIRED_RESOURCES: tuple[str, ...] = (
    # Plantilla base (anteriores)
    "python_ai_template/template/.gitignore",
    "python_ai_template/template/.opencode/.gitignore",
    "python_ai_template/template/pyproject.toml.tmpl",
    ("python_ai_template/template/src/__package_name__/__init__.py.tmpl"),
    "python_ai_template/template/tests/test_smoke.py.tmpl",
    # Capa de exploracion y compactacion distribuida (ADR-012)
    "python_ai_template/template/.opencode/agents/scout.md",
    "python_ai_template/template/.opencode/commands/review.md",
    "python_ai_template/template/.opencode/commands/handoff.md",
    "python_ai_template/template/.opencode/commands/verify.md",
    "python_ai_template/template/.opencode/commands/compact-test.md",
    "python_ai_template/template/.opencode/skills/context-handoff/SKILL.md",
    "python_ai_template/template/.opencode/plugins/structured-compaction.ts",
)


class VerificationError(Exception):
    """Fallo de verificacion del wheel."""


def _read_pyproject_version() -> str:
    data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    project = data.get("project")
    if not isinstance(project, dict) or "version" not in project:
        raise VerificationError(
            "pyproject.toml no contiene [project].version o no es un string"
        )
    version = project["version"]
    if not isinstance(version, str):
        raise VerificationError(
            f"pyproject.toml: project.version debe ser string "
            f"(recibido: {type(version).__name__})"
        )
    if not version:
        raise VerificationError("pyproject.toml: project.version es un string vacio")
    return version


def _read_package_version() -> str:
    if not INIT_PATH.is_file():
        raise VerificationError(f"__init__.py no existe en {INIT_PATH}")
    source = INIT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(INIT_PATH))

    assignments: list[ast.Assign] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__version__":
                assignments.append(node)
                break

    if len(assignments) == 0:
        raise VerificationError(
            "__init__.py no contiene ninguna asignacion a __version__"
        )
    if len(assignments) > 1:
        raise VerificationError(
            f"__init__.py contiene {len(assignments)} asignaciones a "
            "__version__ (se esperaba exactamente una)"
        )

    node = assignments[0]
    value = node.value
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        raise VerificationError("__init__.py: __version__ debe ser un string literal")
    if not value.value:
        raise VerificationError("__init__.py: __version__ es un string literal vacio")
    return value.value


def _find_wheel(expected_version: str) -> Path:
    if not DIST_PATH.is_dir():
        raise VerificationError(f"el directorio dist/ no existe ({DIST_PATH})")
    wheels = sorted(DIST_PATH.glob("*.whl"))
    if len(wheels) == 0:
        raise VerificationError(
            "dist/ no contiene ningun wheel (se esperaba uno); ejecuta 'uv build' antes"
        )
    if len(wheels) > 1:
        nombres = ", ".join(w.name for w in wheels)
        raise VerificationError(
            f"dist/ contiene {len(wheels)} wheels (se esperaba uno): {nombres}"
        )
    wheel = wheels[0]
    expected_prefix = f"{DISTRIBUTION_SLUG}-{expected_version}-"
    if not wheel.name.startswith(expected_prefix):
        raise VerificationError(
            f"el nombre del wheel {wheel.name!r} no comienza por {expected_prefix!r}"
        )
    return wheel


def _extract_wheel_name_version(wheel: Path) -> str:
    """Extrae la version del nombre del wheel.

    Estructura PEP 427::
        {distribution}-{version}(-{build})?-{python_tag}-{abi_tag}-{platform_tag}.whl

    Las tres ultimas componentes separadas por ``-`` son siempre
    ``python_tag``, ``abi_tag`` y ``platform_tag``. La version se reconstruye
    como la union con ``-`` de los segmentos entre el primero y los tres
    ultimos, lo que admite versiones PEP 440 con hyphens (p. ej.
    ``1.0.0-rc1``).
    """
    parts = wheel.stem.split("-")
    if len(parts) < 5:
        raise VerificationError(
            f"el nombre del wheel {wheel.name!r} no tiene la estructura "
            "esperada (al menos 5 segmentos nombre-version-py-abi-plat)"
        )
    return "-".join(parts[1:-3])


def _read_metadata_version(wheel: Path) -> str:
    with zipfile.ZipFile(wheel) as zf:
        metadata_members = sorted(
            name for name in zf.namelist() if name.endswith(".dist-info/METADATA")
        )
        if len(metadata_members) == 0:
            raise VerificationError(
                "el wheel no contiene ningun archivo .dist-info/METADATA"
            )
        if len(metadata_members) > 1:
            raise VerificationError(
                f"el wheel contiene {len(metadata_members)} archivos "
                f".dist-info/METADATA (se esperaba uno): {metadata_members}"
            )
        raw = zf.read(metadata_members[0]).decode("utf-8")

    for line in raw.splitlines():
        if line.startswith("Version:"):
            value = line.split(":", 1)[1].strip()
            if not value:
                raise VerificationError("METADATA: campo Version: vacio")
            return value
    raise VerificationError("METADATA no contiene el campo 'Version:'")


def check_required_resources(wheel: Path) -> list[str]:
    with zipfile.ZipFile(wheel) as zf:
        names = set(zf.namelist())
    return [r for r in REQUIRED_RESOURCES if r not in names]


def _verify(expected_version: str) -> tuple[Path, dict[str, str]]:
    """Lee las cuatro fuentes y devuelve ``(wheel, sources)`` si todo encaja.

    Si alguna fuente no coincide con ``expected_version`` (que es
    ``pyproject.toml``), imprime el error por ``stderr`` y lanza
    :class:`VerificationError` con un mensaje que lista las fuentes
    discrepantes.
    """
    package_version = _read_package_version()
    wheel = _find_wheel(expected_version)
    wheel_name_version = _extract_wheel_name_version(wheel)
    metadata_version = _read_metadata_version(wheel)

    sources = {
        "pyproject.toml": expected_version,
        "__version__": package_version,
        "nombre del wheel": wheel_name_version,
        "METADATA Version": metadata_version,
    }

    differing = sorted({k for k, v in sources.items() if v != expected_version})
    if differing:
        names = ", ".join(differing)
        message = (
            f"las siguientes fuentes de la version no coinciden con "
            f"pyproject.toml ({expected_version!r}): {names}"
        )
        print(f"error: {message}", file=sys.stderr)
        raise VerificationError(message)

    return wheel, sources


def main() -> int:
    print(f"Verificando el wheel de python-ai-template desde {__file__}")
    print("=" * 72)

    try:
        expected_version = _read_pyproject_version()
        wheel, sources = _verify(expected_version)
        missing = check_required_resources(wheel)
    except VerificationError as exc:
        print("=" * 72, file=sys.stderr)
        print(
            f"verificacion del wheel FALLIDA: {exc}",
            file=sys.stderr,
        )
        return 1

    print("Fuentes de la version consultadas:")
    for name, value in sources.items():
        print(f"  - {name:<22}: {value}")
    print()
    print(f"Wheel encontrado: {wheel.name}")
    print()

    if missing:
        print(
            "Faltan recursos obligatorios en el wheel:",
            file=sys.stderr,
        )
        for path in missing:
            print(f"  - {path}", file=sys.stderr)
        return 1

    print("Recursos obligatorios presentes:")
    for path in REQUIRED_RESOURCES:
        print(f"  - {path}")
    print()
    print("=" * 72)
    print("OK: wheel verificado correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
