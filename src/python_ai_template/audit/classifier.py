"""Clasificacion de arquetipos con puntuacion determinista.

Reglas:

    python-package (umbral 4; exige real_package_layout o
    explicit_packages_config):

        - pyproject_with_project: 1
        - build_backend: 1
        - real_package_layout: 3
        - explicit_packages_config: 2

    python-scripts (umbral 2):

        - operational_python_scripts: 2
        - scripts_dir: 1
        - entry_point: 1
        - requirements: 1

    notebooks-and-data (umbral 3):

        - operational_notebooks: 3
        - pipelines: 2
        - operational_sql: 2
        - data_directory: 2

Evidencia bajo ``examples/``, ``samples/``, ``docs/`` o
``tests/fixtures/`` pesa 0.25 y nunca activa una categoria por si sola.

``mixed`` solo aplica si dos categorias superan independientemente su
umbral con al menos una senal de activacion plena.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from typing import Any, cast

from python_ai_template.audit.model import Archetype
from python_ai_template.audit.scanner import ScannedRepository

ARCHETYPES: tuple[str, ...] = (
    "python-package",
    "python-scripts",
    "notebooks-and-data",
    "mixed",
    "unknown",
)

REDUCED_WEIGHT = 0.25


@dataclass(frozen=True)
class CategoryScore:
    name: str
    score: float
    signals: tuple[tuple[str, float], ...]
    activated: bool

    def format(self) -> str:
        parts = [f"{name}={value:g}" for name, value in self.signals]
        return f"{self.name}={self.score:g} [{', '.join(parts)}]"


def _parse_pyproject(content: str | None) -> dict[str, Any]:
    if not content:
        return {}
    try:
        result = tomllib.loads(content)
        assert isinstance(result, dict)
        return result
    except Exception:
        return {}


def _round(value: float) -> float:
    """Redondea a 4 decimales para evitar ruido binario en la suma."""
    return round(value, 4)


def _score_python_package(
    parsed: dict[str, Any], repo: ScannedRepository
) -> CategoryScore:
    signals: list[tuple[str, float]] = []

    project = parsed.get("project") if parsed else None
    if isinstance(project, dict) and project:
        signals.append(("pyproject_with_project", 1.0))
        # project no se usa mas para acceder a .get() aqui

    build_system = parsed.get("build-system") if parsed else None
    if isinstance(build_system, dict) and build_system:
        signals.append(("build_backend", 1.0))

    if repo.src_layout_dirs or repo.top_level_packages:
        signals.append(("real_package_layout", 3.0))

    has_explicit_packages = False
    tool = parsed.get("tool") if parsed else None
    if isinstance(tool, dict):
        td = cast(dict[str, Any], tool)
        setuptools = td.get("setuptools")
        if isinstance(setuptools, dict) and "packages" in setuptools:
            has_explicit_packages = True
        hatch = td.get("hatch")
        if isinstance(hatch, dict):
            hd = cast(dict[str, Any], hatch)
            build = hd.get("build")
            if isinstance(build, dict) and "targets" in build:
                has_explicit_packages = True
    if has_explicit_packages:
        signals.append(("explicit_packages_config", 2.0))

    signals.sort(key=lambda item: item[0])
    score = _round(sum(value for _, value in signals))

    has_layout = bool(repo.src_layout_dirs or repo.top_level_packages)
    has_explicit = has_explicit_packages
    score_activated = score >= 4 and (has_layout or has_explicit)

    return CategoryScore(
        name="python-package",
        score=score,
        signals=tuple(signals),
        activated=score_activated,
    )


def _score_python_scripts(
    parsed: dict[str, Any], repo: ScannedRepository
) -> CategoryScore:
    signals: list[tuple[str, float]] = []
    project = parsed.get("project") if parsed else None

    if repo.operational_python_count > 0:
        signals.append(("operational_python_scripts", 2.0))

    if repo.scripts_dir:
        signals.append(("scripts_dir", 1.0))

    has_entry_point = False
    if isinstance(project, dict):
        pd = cast(dict[str, Any], project)
        scripts = pd.get("scripts")
        gui_scripts = pd.get("gui-scripts")
        if isinstance(scripts, dict) and scripts:
            has_entry_point = True
        if isinstance(gui_scripts, dict) and gui_scripts:
            has_entry_point = True
    if has_entry_point:
        signals.append(("entry_point", 1.0))

    if repo.requirements_files:
        signals.append(("requirements", 1.0))

    signals.sort(key=lambda item: item[0])
    score = _round(sum(value for _, value in signals))
    activated = score >= 2

    return CategoryScore(
        name="python-scripts",
        score=score,
        signals=tuple(signals),
        activated=activated,
    )


def _score_notebooks_and_data(repo: ScannedRepository) -> CategoryScore:
    signals: list[tuple[str, float]] = []
    activated = False

    if repo.notebooks_operational > 0:
        signals.append(("operational_notebooks", 3.0))
        activated = True
    elif repo.notebooks_in_examples > 0:
        signals.append(
            (
                "operational_notebooks_reduced",
                3.0 * REDUCED_WEIGHT,
            )
        )

    if repo.pipeline_dirs:
        signals.append(("pipelines", 2.0))
        activated = True

    if repo.sql_operational > 0:
        signals.append(("operational_sql", 2.0))
        activated = True

    if repo.data_dirs:
        signals.append(("data_directory", 2.0))
        activated = True

    signals.sort(key=lambda item: item[0])
    score = _round(sum(value for _, value in signals))
    score_activated = score >= 3 and activated

    return CategoryScore(
        name="notebooks-and-data",
        score=score,
        signals=tuple(signals),
        activated=score_activated,
    )


def classify(repo: ScannedRepository) -> Archetype:
    """Devuelve el arquetipo detectado y la rationale determinista."""
    parsed = _parse_pyproject(repo.pyproject_content)

    pkg = _score_python_package(parsed, repo)
    scripts = _score_python_scripts(parsed, repo)
    ndata = _score_notebooks_and_data(repo)

    activated_count = sum(1 for cat in (pkg, scripts, ndata) if cat.activated)

    if activated_count >= 2:
        classification = "mixed"
        rationale = "; ".join(
            cat.format() for cat in (pkg, scripts, ndata) if cat.activated
        )
    elif pkg.activated:
        classification = "python-package"
        rationale = pkg.format()
    elif scripts.activated:
        classification = "python-scripts"
        rationale = scripts.format()
    elif ndata.activated:
        classification = "notebooks-and-data"
        rationale = ndata.format()
    else:
        classification = "unknown"
        rationale = "no category activated"

    return Archetype(classification=classification, rationale=rationale)
