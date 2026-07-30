"""Dataclasses inmutables que representan el schema del manifest de audit.

El schema es el acordado en la primera unidad y esta congelado para esta
unidad. Cambios requieren nueva ADR.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = 1
TEMPLATE_VERSION = "0.3.3"
OPERATION_AUDIT = "audit"


@dataclass(frozen=True)
class Repository:
    path: str = "."


@dataclass(frozen=True)
class Git:
    head: str
    branch: str
    porcelain_clean: bool
    untracked_count: int
    modified_count: int


@dataclass(frozen=True)
class Authority:
    agents_md: str | None = None
    readme: tuple[str, ...] = ()
    adr: tuple[str, ...] = ()
    architecture_doc: tuple[str, ...] = ()
    contracts: tuple[str, ...] = ()


@dataclass(frozen=True)
class Archetype:
    classification: str
    rationale: str


@dataclass(frozen=True)
class RuntimePython:
    version_hint: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class RuntimeNotebooks:
    count: int = 0


@dataclass(frozen=True)
class RuntimeSql:
    count: int = 0


@dataclass(frozen=True)
class Tooling:
    package_managers: tuple[str, ...] = ()
    linters: tuple[str, ...] = ()
    formatters: tuple[str, ...] = ()
    type_checkers: tuple[str, ...] = ()
    test_runners: tuple[str, ...] = ()
    quality_gates_declared: tuple[str, ...] = ()


@dataclass(frozen=True)
class CIGitHubActions:
    workflow_files: tuple[str, ...] = ()


@dataclass(frozen=True)
class Integration:
    evidence: tuple[str, ...]
    confidence: str


@dataclass(frozen=True)
class QualitySurface:
    note: str
    suggested_validated_paths: tuple[str, ...]
    suggested_excluded_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class Finding:
    id: str
    category: str
    severity: str
    path: str | None = None
    line: int | None = None
    match: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class Unknown:
    id: str
    kind: str
    category: str | None = None
    count: int | None = None
    path: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class Conflict:
    id: str
    between: tuple[str, ...]
    summary: str
    suggested_resolution: str | None = None


@dataclass(frozen=True)
class AuditResult:
    schema_version: int
    template_version: str
    operation: str
    repository: Repository
    archetype: Archetype
    git: Git | None = None
    authority: Authority = field(default_factory=Authority)
    detected_runtimes: dict[str, Any] = field(default_factory=dict[str, Any])
    detected_tooling: Tooling = field(default_factory=Tooling)
    detected_ci: dict[str, Any] = field(default_factory=dict[str, Any])
    detected_integrations: dict[str, Integration] = field(
        default_factory=dict[str, Integration]
    )
    quality_surface_proposed: QualitySurface | None = None
    findings: tuple[Finding, ...] = ()
    unknowns: tuple[Unknown, ...] = ()
    conflicts: tuple[Conflict, ...] = ()
