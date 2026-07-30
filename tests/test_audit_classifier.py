"""Tests del classifier (senales, puntuacion y arquetipo).

Construye cada fixture con ``tmp_path``. Verifica:

    - paquete real (pyproject + src layout);
    - scripts sin pyproject.toml;
    - notebooks y datos operativos;
    - paquete con notebook solo en ``examples/`` permanece ``python-package``;
    - paquete con notebook operativo pasa a ``mixed``;
    - ``unknown`` para arbol sin senales;
    - ``rationale`` igual a la suma real;
    - orden determinista de senales.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


from python_ai_template.audit.classifier import classify  # noqa: E402
from python_ai_template.audit.scanner import ScannedRepository, scan  # noqa: E402


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scan(tmp_path: Path) -> ScannedRepository:
    return scan(tmp_path)


# 1. python-package clasico.
def test_classifies_real_package(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        '[build-system]\nrequires=["hatchling"]\nbuild-backend="hatchling.build"\n\n'
        '[project]\nname="x"\nversion="0.1.0"\nrequires-python=">=3.12"\n',
    )
    _write(tmp_path / "src" / "mypkg" / "__init__.py")
    result = classify(_scan(tmp_path))
    assert result.classification == "python-package"
    assert "real_package_layout=3" in result.rationale
    assert "pyproject_with_project=1" in result.rationale
    assert "build_backend=1" in result.rationale


# 2. python-scripts sin pyproject.toml.
def test_classifies_scripts_without_pyproject(tmp_path: Path) -> None:
    _write(tmp_path / "scripts" / "run.py")
    _write(tmp_path / "requirements.txt", "requests\n")
    result = classify(_scan(tmp_path))
    assert result.classification == "python-scripts"
    assert "scripts_dir=1" in result.rationale
    assert "requirements=1" in result.rationale


# 3. notebooks-and-data operativo.
def test_classifies_operational_notebooks_and_data(tmp_path: Path) -> None:
    _write(tmp_path / "notebooks" / "01_ingesta.ipynb", "{}")
    _write(tmp_path / "data" / "raw.csv", "a,b\n1,2\n")
    result = classify(_scan(tmp_path))
    assert result.classification == "notebooks-and-data"
    assert "operational_notebooks=3" in result.rationale
    assert "data_directory=2" in result.rationale


# 4. paquete con notebook solo en examples/ permanece python-package.
def test_package_with_examples_notebook_stays_package(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        '[build-system]\nrequires=["hatchling"]\nbuild-backend="hatchling.build"\n\n'
        '[project]\nname="x"\nversion="0.1.0"\nrequires-python=">=3.12"\n',
    )
    _write(tmp_path / "src" / "mypkg" / "__init__.py")
    _write(tmp_path / "examples" / "demo.ipynb", "{}")
    result = classify(_scan(tmp_path))
    assert result.classification == "python-package"


# 5. paquete con notebook operativo pasa a mixed.
def test_package_with_operational_notebook_becomes_mixed(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        '[build-system]\nrequires=["hatchling"]\nbuild-backend="hatchling.build"\n\n'
        '[project]\nname="x"\nversion="0.1.0"\nrequires-python=">=3.12"\n',
    )
    _write(tmp_path / "src" / "mypkg" / "__init__.py")
    _write(tmp_path / "notebooks" / "01_ingesta.ipynb", "{}")
    result = classify(_scan(tmp_path))
    assert result.classification == "mixed"
    assert "python-package=" in result.rationale
    assert "notebooks-and-data=" in result.rationale


# 6. unknown para arbol vacio de senales.
def test_unknown_when_no_signals(tmp_path: Path) -> None:
    result = classify(_scan(tmp_path))
    assert result.classification == "unknown"


# 7. rationale: score real igual a suma de senales.
def test_rationale_score_equals_sum_of_signals(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        '[build-system]\nrequires=["hatchling"]\nbuild-backend="hatchling.build"\n\n'
        '[project]\nname="x"\nversion="0.1.0"\nrequires-python=">=3.12"\n'
        '[tool.setuptools]\npackages=["x"]\n',
    )
    _write(tmp_path / "src" / "mypkg" / "__init__.py")
    result = classify(_scan(tmp_path))
    assert result.classification == "python-package"
    prefix, _, body = result.rationale.partition("[")
    score_str = prefix.split("=")[1]
    score = float(score_str)
    parts = [p.strip() for p in body.rstrip("]").split(",")]
    summed = sum(float(p.split("=")[1]) for p in parts)
    assert abs(score - summed) < 1e-6


# 8. orden determinista de senales en rationale.
def test_rationale_signal_order_is_deterministic(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        '[build-system]\nrequires=["hatchling"]\nbuild-backend="hatchling.build"\n\n'
        '[project]\nname="x"\nversion="0.1.0"\nrequires-python=">=3.12"\n',
    )
    _write(tmp_path / "src" / "mypkg" / "__init__.py")
    _write(tmp_path / "tests" / "test_smoke.py")
    first = classify(_scan(tmp_path)).rationale
    second = classify(_scan(tmp_path)).rationale
    assert first == second


# 9. directorio de datos por si solo no alcanza el umbral.
def test_data_dir_alone_does_not_reach_threshold(tmp_path: Path) -> None:
    _write(tmp_path / "data" / "raw.csv", "a,b\n1,2\n")
    result = classify(_scan(tmp_path))
    assert result.classification == "unknown"
    assert result.rationale == "no category activated"


# 10. SQL operativo + pipelines activa notebooks-and-data.
def test_sql_and_pipelines_activate(tmp_path: Path) -> None:
    _write(tmp_path / "pipelines" / "dag.py", "")
    _write(tmp_path / "migrations" / "0001_init.sql", "CREATE TABLE x(id INT);")
    result = classify(_scan(tmp_path))
    assert result.classification == "mixed"
    assert "notebooks-and-data=4" in result.rationale
    assert "python-scripts=2" in result.rationale


# 11. paquete real + pipelines = mixed.
def test_real_package_plus_pipelines_is_mixed(tmp_path: Path) -> None:
    _write(
        tmp_path / "pyproject.toml",
        '[build-system]\nrequires=["hatchling"]\nbuild-backend="hatchling.build"\n\n'
        '[project]\nname="x"\nversion="0.1.0"\nrequires-python=">=3.12"\n',
    )
    _write(tmp_path / "src" / "mypkg" / "__init__.py")
    _write(tmp_path / "pipelines" / "dag.py", "")
    result = classify(_scan(tmp_path))
    assert result.classification == "mixed"
