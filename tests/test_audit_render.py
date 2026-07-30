"""Tests del renderer TOML.

Verifica:

    - salida parseable con ``tomllib.loads``;
    - orden determinista de claves, subtablas y arrays;
    - arrays de tablas (``[[findings]]`` etc.);
    - escape correcto de strings;
    - omision de campos opcionales cuando estan vacios;
    - ausencia de ``null``, ``[meta]`` y ``audit_version``;
    - integraciones siempre con evidencia no vacia.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


from typing import Any

from python_ai_template.audit.model import (  # noqa: E402
    Archetype,
    AuditResult,
    Authority,
    CIGitHubActions,
    Conflict,
    Finding,
    Git,
    Integration,
    QualitySurface,
    Repository,
    RuntimeNotebooks,
    RuntimePython,
    Tooling,
    Unknown,
)
from python_ai_template.audit.render import render  # noqa: E402


def _minimal(
    *,
    archetype_cls: str = "python-package",
    rationale: str = (
        "python-package=5 "
        "[build_backend=1, pyproject_with_project=1, real_package_layout=3]"
    ),
    git: Git | None = None,
    authority: Authority | None = None,
    runtimes: dict[str, Any] | None = None,
    tooling: Tooling | None = None,
    ci: dict[str, Any] | None = None,
    integrations: dict[str, Integration] | None = None,
    quality: QualitySurface | None = None,
    findings: tuple[Finding, ...] = (),
    unknowns: tuple[Unknown, ...] = (),
    conflicts: tuple[Conflict, ...] = (),
) -> AuditResult:
    return AuditResult(
        schema_version=1,
        template_version="0.3.3",
        operation="audit",
        repository=Repository(),
        archetype=Archetype(classification=archetype_cls, rationale=rationale),
        git=git,
        authority=authority or Authority(),
        detected_runtimes=runtimes or dict[str, Any](),
        detected_tooling=tooling or Tooling(),
        detected_ci=ci or dict[str, Any](),
        detected_integrations=integrations or dict[str, Integration](),
        quality_surface_proposed=quality,
        findings=findings,
        unknowns=unknowns,
        conflicts=conflicts,
    )


# 1. salida parseable con tomllib.loads.
def test_render_is_valid_toml() -> None:
    out = render(_minimal())
    parsed = tomllib.loads(out)
    assert parsed["schema_version"] == 1
    assert parsed["template_version"] == "0.3.3"
    assert parsed["operation"] == "audit"


# 2. orden determinista de claves top-level.
def test_render_top_level_order_is_stable() -> None:
    a = render(_minimal())
    b = render(_minimal())
    assert a == b


# 3. orden determinista de subtablas de detected_runtimes.
def test_render_runtimes_order_alphabetical() -> None:
    result = _minimal(
        runtimes={
            "sql": RuntimeNotebooks(count=1),
            "notebooks": RuntimeNotebooks(count=2),
            "python": RuntimePython(version_hint=">=3.12", source="pyproject.toml"),
        }
    )
    out = render(result)
    pos_n = out.index("[detected_runtimes.notebooks]")
    pos_p = out.index("[detected_runtimes.python]")
    pos_s = out.index("[detected_runtimes.sql]")
    assert pos_n < pos_p < pos_s


# 4. arrays de tablas [[findings]] ordenados por id.
def test_render_findings_sorted_by_id() -> None:
    result = _minimal(
        findings=(
            Finding(id="FIND-002", category="x", severity="info"),
            Finding(id="FIND-001", category="x", severity="info"),
            Finding(id="FIND-010", category="x", severity="info"),
        )
    )
    out = render(result)
    pos_001 = out.index('id = "FIND-001"')
    pos_002 = out.index('id = "FIND-002"')
    pos_010 = out.index('id = "FIND-010"')
    assert pos_001 < pos_002 < pos_010


# 5. escape correcto de strings con caracteres especiales.
def test_render_string_escape() -> None:
    result = _minimal(
        archetype_cls='package"with"quote',
        rationale="has \\backslash",
    )
    out = render(result)
    parsed = tomllib.loads(out)
    assert parsed["archetype"]["classification"] == 'package"with"quote'
    assert parsed["archetype"]["rationale"] == "has \\backslash"


# 6. omision de campos opcionales cuando son None o vacios.
def test_render_omits_empty_fields() -> None:
    result = _minimal(authority=Authority())
    out = render(result)
    assert "[authority]" not in out
    parsed = tomllib.loads(out)
    assert "authority" not in parsed


# 7. ausencia de "null", [meta], audit_version.
def test_render_no_null_meta_audit_version() -> None:
    out = render(_minimal())
    assert "null" not in out
    assert "[meta]" not in out
    assert "audit_version" not in out


# 8. integracion con evidencia vacia NO se emite.
def test_render_skips_integration_with_empty_evidence() -> None:
    result = _minimal(
        integrations={
            "fabric": Integration(evidence=(), confidence="low"),
            "azure": Integration(evidence=("pyproject.toml",), confidence="high"),
        }
    )
    out = render(result)
    parsed = tomllib.loads(out)
    assert "fabric" not in parsed.get("detected_integrations", {})
    assert "azure" in parsed.get("detected_integrations", {})


# 9. quality_surface_proposed omitido si es None.
def test_render_no_quality_surface_when_none() -> None:
    out = render(_minimal(quality=None))
    assert "[quality_surface_proposed]" not in out


# 10. quality_surface_proposed se serializa cuando existe.
def test_render_quality_surface_serializes() -> None:
    from python_ai_template.audit.model import QualitySurface

    qs = QualitySurface(
        note="Provisional. No claim of validation.",
        suggested_validated_paths=("src/x/",),
        suggested_excluded_paths=("notebooks/",),
    )
    out = render(_minimal(quality=qs))
    parsed = tomllib.loads(out)
    assert "quality_surface_proposed" in parsed
    assert (
        parsed["quality_surface_proposed"]["note"]
        == "Provisional. No claim of validation."
    )


# 11. CI detected_ci se serializa como subtabla.
def test_render_ci_subtable() -> None:
    result = _minimal(
        ci={"github_actions": CIGitHubActions(workflow_files=("ci.yml",))}
    )
    out = render(result)
    parsed = tomllib.loads(out)
    assert "github_actions" in parsed["detected_ci"]
    assert parsed["detected_ci"]["github_actions"]["workflow_files"] == ["ci.yml"]


# 12. Git opcional se serializa solo si esta presente.
def test_render_git_optional() -> None:
    from python_ai_template.audit.model import Git

    g = Git(
        head="abc123",
        branch="main",
        porcelain_clean=True,
        untracked_count=0,
        modified_count=0,
    )
    out = render(_minimal(git=g))
    parsed = tomllib.loads(out)
    assert parsed["git"]["head"] == "abc123"
    assert parsed["git"]["branch"] == "main"


# 13. ausencia de git omite la seccion.
def test_render_no_git_omits_section() -> None:
    out = render(_minimal(git=None))
    parsed = tomllib.loads(out)
    assert "git" not in parsed


# 14. unknowns serializados ordenados por id.
def test_render_unknowns_sorted_by_id() -> None:
    result = _minimal(
        unknowns=(
            Unknown(id="UNK-002", kind="x"),
            Unknown(id="UNK-001", kind="y"),
        )
    )
    out = render(result)
    pos_001 = out.index('id = "UNK-001"')
    pos_002 = out.index('id = "UNK-002"')
    assert pos_001 < pos_002


# 15. conflicts serializados con between como tuple.
def test_render_conflicts_with_between_tuple() -> None:
    result = _minimal(
        conflicts=(
            Conflict(
                id="CONF-001",
                between=(
                    'pyproject.toml [project] requires-python = ">=3.12"',
                    '.github/workflows/ci.yml: python-version = "3.11"',
                ),
                summary="version minima no coincide",
                suggested_resolution="alinear",
            ),
        )
    )
    out = render(result)
    parsed = tomllib.loads(out)
    assert parsed["conflicts"][0]["between"] == [
        'pyproject.toml [project] requires-python = ">=3.12"',
        '.github/workflows/ci.yml: python-version = "3.11"',
    ]
