"""Tests del verificador del wheel (``verify_wheel.py``).

Tests hermeticos: construyen un wheel sintetico en ``tmp_path``
usando ``zipfile`` (sin ejecutar ``uv build``) y verifican que el
validador exige los 12 recursos obligatorios.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "tools" / "ai"),
)

import verify_wheel as vw  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_minimal_wheel(
    wheel_path: Path,
    *,
    missing: set[str] | None = None,
    version: str = "0.3.2",
) -> None:
    """Crea un wheel sintetico con los 12 recursos obligatorios.

    Si ``missing`` contiene rutas, esas se omiten. Las rutas deben
    coincidir con las entradas de ``REQUIRED_RESOURCES``.
    """
    missing = missing or set()
    with zipfile.ZipFile(wheel_path, "w") as zf:
        for resource in vw.REQUIRED_RESOURCES:
            if resource in missing:
                continue
            zf.writestr(resource, f"# contenido de {resource}\n")

        # Anadir un METADATA con la version correcta
        metadata = (
            f"Metadata-Version: 2.1\nName: {vw.DISTRIBUTION_SLUG}\nVersion: {version}\n"
        )
        zf.writestr(
            f"{vw.DISTRIBUTION_SLUG}-{version}.dist-info/METADATA",
            metadata,
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_required_resources_count() -> None:
    """12 recursos: 5 originales + 7 de la capa de exploracion."""
    assert len(vw.REQUIRED_RESOURCES) == 12


def test_required_resources_includes_seven_opencode() -> None:
    expected_suffixes = (
        "/.opencode/agents/scout.md",
        "/.opencode/commands/review.md",
        "/.opencode/commands/handoff.md",
        "/.opencode/commands/verify.md",
        "/.opencode/commands/compact-test.md",
        "/.opencode/skills/context-handoff/SKILL.md",
        "/.opencode/plugins/structured-compaction.ts",
    )
    for suffix in expected_suffixes:
        assert any(r.endswith(suffix) for r in vw.REQUIRED_RESOURCES), suffix


def test_check_required_resources_ok(tmp_path: Path) -> None:
    wheel = tmp_path / "wheel.whl"
    _write_minimal_wheel(wheel)
    missing = vw.check_required_resources(wheel)
    assert missing == []


def test_check_required_resources_missing_one(tmp_path: Path) -> None:
    wheel = tmp_path / "wheel.whl"
    _write_minimal_wheel(
        wheel, missing={"python_ai_template/template/.opencode/agents/scout.md"}
    )
    missing = vw.check_required_resources(wheel)
    assert "python_ai_template/template/.opencode/agents/scout.md" in missing


def test_check_required_resources_missing_plugin(tmp_path: Path) -> None:
    wheel = tmp_path / "wheel.whl"
    _write_minimal_wheel(
        wheel,
        missing={
            "python_ai_template/template/.opencode/plugins/structured-compaction.ts"
        },
    )
    missing = vw.check_required_resources(wheel)
    assert any("structured-compaction.ts" in m for m in missing)


def test_check_required_resources_missing_compact_test(tmp_path: Path) -> None:
    wheel = tmp_path / "wheel.whl"
    _write_minimal_wheel(
        wheel,
        missing={"python_ai_template/template/.opencode/commands/compact-test.md"},
    )
    missing = vw.check_required_resources(wheel)
    assert any("compact-test.md" in m for m in missing)


def test_full_verify_ok(tmp_path: Path) -> None:
    """Wheel sintetico con todos los recursos -> 0 missing."""
    wheel = tmp_path / "wheel.whl"
    _write_minimal_wheel(wheel, version="0.3.2")
    missing = vw.check_required_resources(wheel)
    assert missing == []


def test_full_verify_missing_resource(tmp_path: Path) -> None:
    """Wheel sin un recurso -> ese recurso aparece como missing."""
    wheel = tmp_path / "wheel.whl"
    _write_minimal_wheel(
        wheel,
        version="0.3.2",
        missing={"python_ai_template/template/.opencode/commands/compact-test.md"},
    )
    missing = vw.check_required_resources(wheel)
    assert len(missing) == 1
    assert "compact-test.md" in missing[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
