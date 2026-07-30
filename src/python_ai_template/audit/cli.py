"""CLI del subcomando ``audit``.

Parsea argumentos, valida el target, delega en scanner y classifier y
emite el manifest TOML a ``stdout`` o a ``--output`` (escritura atomica
fuera del repositorio auditado).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, cast

from python_ai_template.audit.classifier import classify
from python_ai_template.audit.model import (
    AuditResult,
    Authority,
    Conflict,
    Finding,
    Integration,
    QualitySurface,
    Repository,
    RuntimeNotebooks,
    RuntimePython,
    RuntimeSql,
    Tooling,
    Unknown,
)
from python_ai_template.audit.render import render
from python_ai_template.audit.scanner import ScannedRepository, scan


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python-ai-template audit",
        description=(
            "Inspecciona un repositorio sin modificarlo y emite un "
            "manifest TOML con la clasificacion del arquetipo, "
            "integraciones detectadas, findings, unknowns y conflicts."
        ),
    )
    parser.add_argument(
        "repository",
        help="ruta al repositorio a auditar",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "ruta externa donde escribir el manifest; debe resolverse "
            "fuera del repositorio auditado"
        ),
    )
    return parser


def _validate_target(repository: str) -> Path | None:
    target = Path(repository).resolve(strict=False)
    if not target.exists():
        print(f"error: la ruta {target} no existe", file=sys.stderr)
        return None
    if not target.is_dir():
        print(
            f"error: la ruta {target} existe pero no es un directorio",
            file=sys.stderr,
        )
        return None
    return target


def _validate_output(target: Path, output: str | None) -> Path | None:
    if output is None:
        return None
    output_path = Path(output).resolve(strict=False)
    if output_path == target:
        print(
            f"error: --output {output_path} coincide con el repositorio "
            "auditado; debe ser una ruta externa",
            file=sys.stderr,
        )
        return None
    try:
        target_resolved = target.resolve()
    except OSError:
        target_resolved = target
    try:
        output_resolved = output_path.resolve()
    except OSError:
        output_resolved = output_path
    if output_resolved == target_resolved:
        print(
            f"error: --output resuelto {output_resolved} coincide con el target",
            file=sys.stderr,
        )
        return None
    if target_resolved in output_resolved.parents:
        print(
            f"error: --output resuelto {output_resolved} esta dentro del "
            "target; debe ser externo",
            file=sys.stderr,
        )
        return None
    parent = output_path.parent
    if not parent.exists():
        print(
            f"error: el directorio padre de --output {parent} no existe",
            file=sys.stderr,
        )
        return None
    if not parent.is_dir():
        print(
            f"error: la ruta padre de --output {parent} no es un directorio",
            file=sys.stderr,
        )
        return None
    return output_path


def _build_authority(repo: ScannedRepository) -> Authority:
    agents_md = None
    if "AGENTS.md" in repo.allowlisted_docs_read:
        agents_md = "AGENTS.md"
    readme: list[str] = []
    for rel in repo.allowlisted_docs_read:
        name = Path(rel).name
        if name.startswith("README"):
            readme.append(rel)
    readme.sort()
    adr: list[str] = []
    for rel in repo.allowlisted_docs_read:
        name = Path(rel).name
        top = rel.split("/", 1)[0] if "/" in rel else ""
        if name == "decisions.md" and top == "docs":
            adr.append(rel)
        elif top == "docs" and "adr" in rel.split("/"):
            adr.append(rel)
    adr.sort()
    arch: list[str] = []
    for rel in repo.allowlisted_docs_read:
        name = Path(rel).name
        top = rel.split("/", 1)[0] if "/" in rel else ""
        if name in {"architecture.md", "ARCHITECTURE.md"}:
            arch.append(rel)
        elif top == "docs" and "architecture" in rel.split("/"):
            arch.append(rel)
    arch.sort()
    contracts: list[str] = []
    for rel in repo.allowlisted_docs_read:
        name = Path(rel).name
        if name.startswith(("CONTRACT", "CONTRACTS", "PROCESO")):
            contracts.append(rel)
        elif rel.startswith("docs/contracts/") and name.endswith(".md"):
            contracts.append(rel)
    contracts.sort()
    return Authority(
        agents_md=agents_md,
        readme=tuple(readme),
        adr=tuple(adr),
        architecture_doc=tuple(arch),
        contracts=tuple(contracts),
    )


def _build_tooling(repo: ScannedRepository) -> Tooling:
    pkg_managers: list[str] = []
    linters: list[str] = []
    formatters: list[str] = []
    type_checkers: list[str] = []
    test_runners: list[str] = []
    gates: list[str] = []

    for path in repo.allowlisted_config_read:
        name = Path(path).name
        if name == "uv.lock":
            if "uv" not in pkg_managers:
                pkg_managers.append("uv")
        if name == "pyproject.toml":
            text = repo.allowlisted_config_read[path].lower()
            if "[tool.ruff]" in text or "ruff" in text:
                if "ruff" not in linters:
                    linters.append("ruff")
                if "ruff" not in formatters:
                    formatters.append("ruff")
            if "[tool.pyright]" in text or "pyright" in text:
                if "pyright" not in type_checkers:
                    type_checkers.append("pyright")
            if "[tool.mypy]" in text or "mypy" in text:
                if "mypy" not in type_checkers:
                    type_checkers.append("mypy")
            if "[tool.pytest" in text or "pytest" in text:
                if "pytest" not in test_runners:
                    test_runners.append("pytest")
        if name in {
            "requirements.txt",
            "requirements.in",
            "requirements-dev.txt",
            "requirements-lint.txt",
        }:
            text = repo.allowlisted_config_read[path].lower()
            if "pip" not in pkg_managers and any(
                token in text for token in ("pip", "install", "freeze")
            ):
                pkg_managers.append("pip")
            if "pytest" in text and "pytest" not in test_runners:
                test_runners.append("pytest")
        if name == ".pre-commit-config.yaml":
            text = repo.allowlisted_config_read[path].lower()
            for token in ("ruff", "mypy", "pyright", "black", "flake8", "bandit"):
                if token in text and token not in linters:
                    linters.append(token)

    for _path, text in repo.ci_files_read.items():
        lowered = text.lower()
        if "ruff check" in lowered and "ruff check" not in gates:
            gates.append("ruff check")
        if "ruff format --check" in lowered and "ruff format --check" not in gates:
            gates.append("ruff format --check")
        if "pyright" in lowered and "pyright" not in gates:
            gates.append("pyright")
        if "pytest" in lowered and "pytest" not in gates:
            gates.append("pytest")

    return Tooling(
        package_managers=tuple(sorted(pkg_managers)),
        linters=tuple(sorted(linters)),
        formatters=tuple(sorted(formatters)),
        type_checkers=tuple(sorted(type_checkers)),
        test_runners=tuple(sorted(test_runners)),
        quality_gates_declared=tuple(sorted(gates)),
    )


def _build_ci(repo: ScannedRepository) -> dict[str, object]:
    ci: dict[str, object] = {}
    gh_workflows = sorted(
        rel for rel in repo.ci_workflows if rel.startswith(".github/workflows/")
    )
    if gh_workflows:
        ci["github_actions"] = {"workflow_files": tuple(gh_workflows)}
    other: list[str] = []
    for rel in repo.ci_workflows:
        if not rel.startswith(".github/workflows/"):
            other.append(rel)
    if other:
        ci["other"] = {"candidates": tuple(sorted(other))}
    return ci


def _build_runtimes(repo: ScannedRepository) -> dict[str, object]:
    runtimes: dict[str, object] = {}
    if repo.has_pyproject and repo.pyproject_content is not None:
        import tomllib

        try:
            parsed: dict[str, Any] = tomllib.loads(repo.pyproject_content)
        except Exception:
            parsed: dict[str, Any] = {}
        project = parsed.get("project")
        if isinstance(project, dict):
            pd: dict[str, Any] = cast(dict[str, Any], project)
            version_hint = pd.get("requires-python")
            runtimes["python"] = RuntimePython(
                version_hint=version_hint if isinstance(version_hint, str) else None,
                source="pyproject.toml",
            )
    if repo.notebooks_total > 0:
        runtimes["notebooks"] = RuntimeNotebooks(count=repo.notebooks_total)
    if repo.sql_total > 0:
        runtimes["sql"] = RuntimeSql(count=repo.sql_total)
    return runtimes


def _build_integrations(repo: ScannedRepository) -> dict[str, Integration]:
    integrations: dict[str, Integration] = {}
    for name in sorted(repo.integrations_evidence):
        evidence = sorted(set(repo.integrations_evidence[name]))
        if not evidence:
            continue
        confidence = (
            "high"
            if len(evidence) >= 3
            else ("medium" if len(evidence) == 2 else "low")
        )
        integrations[name] = Integration(
            evidence=tuple(evidence),
            confidence=confidence,
        )
    return integrations


def _build_findings_and_unknowns(
    repo: ScannedRepository,
    authority: Authority,
    tooling: Tooling,
    ci_versions: list[str],
) -> tuple[list[Finding], list[Unknown], list[Conflict]]:
    findings: list[Finding] = []
    unknowns: list[Unknown] = []
    counter = {"F": 0, "U": 0, "C": 0}

    def next_fid() -> str:
        counter["F"] += 1
        return f"FIND-{counter['F']:03d}"

    def next_uid() -> str:
        counter["U"] += 1
        return f"UNK-{counter['U']:03d}"

    def next_cid() -> str:
        counter["C"] += 1
        return f"CONF-{counter['C']:03d}"

    for symlink in sorted(repo.symlinks):
        findings.append(
            Finding(
                id=next_fid(),
                category="suspicious-config",
                severity="warning",
                path=symlink,
                note="symlink skipped",
            )
        )

    if authority.agents_md is None and (tooling.quality_gates_declared or ci_versions):
        findings.append(
            Finding(
                id=next_fid(),
                category="suspicious-config",
                severity="notice",
                note=("AGENTS.md ausente mientras existen quality gates declarados"),
            )
        )

    for ver in ci_versions:
        if not ver.startswith(("3.10", "3.11", "3.12", "3.13", "3.14")):
            findings.append(
                Finding(
                    id=next_fid(),
                    category="undeclared-tool",
                    severity="info",
                    note=f"CI declara python-version no soportada: {ver}",
                )
            )

    if repo.truncated:
        unknowns.append(
            Unknown(
                id=next_uid(),
                kind="evidence-insufficient",
                note="limit MAX_FILES o MAX_DEPTH alcanzado",
            )
        )

    if repo.git_unavailable:
        unknowns.append(
            Unknown(
                id=next_uid(),
                kind="git-unavailable",
                note="git no disponible o .git ausente",
            )
        )

    denylist_categories = sorted(
        cat for cat in repo.denylist_counts if cat != "data-tabular-large"
    )
    for cat in denylist_categories:
        count = repo.denylist_counts[cat]
        unknowns.append(
            Unknown(
                id=next_uid(),
                kind="denylisted-path-count",
                category=cat,
                count=count,
            )
        )
    if "data-tabular-large" in repo.denylist_counts:
        unknowns.append(
            Unknown(
                id=next_uid(),
                kind="denylisted-path-count",
                category="data-tabular-large",
                count=repo.denylist_counts["data-tabular-large"],
            )
        )

    detected_python = None
    if repo.has_pyproject and repo.pyproject_content is not None:
        import tomllib

        try:
            parsed: dict[str, Any] = tomllib.loads(repo.pyproject_content)
            project = parsed.get("project")
            if isinstance(project, dict):
                pd: dict[str, Any] = cast(dict[str, Any], project)
                rp = pd.get("requires-python")
                if isinstance(rp, str):
                    detected_python = rp
        except Exception:
            detected_python = None

    conflicts: list[Conflict] = []
    if detected_python is not None and ci_versions:
        import re as _re

        m = _re.search(r">=\s*([0-9.]+)", detected_python)
        if m:
            min_py = m.group(1)

            def _to_tuple(v: str) -> tuple[int, ...]:
                parts: list[int] = []
                for token in v.split("."):
                    digits = ""
                    for ch in token:
                        if ch.isdigit():
                            digits += ch
                        else:
                            break
                    if digits:
                        parts.append(int(digits))
                return tuple(parts)

            min_tuple = _to_tuple(min_py)
            seen_pairs: set[tuple[str, str]] = set()
            for ci_file, ci_text in sorted(repo.ci_files_read.items()):
                for ci_ver in _re.findall(
                    r"python-version:\s*[\"']?([0-9.]+)[\"']?", ci_text
                ):
                    ci_tuple = _to_tuple(ci_ver)
                    if ci_tuple and min_tuple and ci_tuple < min_tuple:
                        key = (detected_python, ci_ver)
                        if key in seen_pairs:
                            continue
                        seen_pairs.add(key)
                        conflicts.append(
                            Conflict(
                                id=next_cid(),
                                between=(
                                    "pyproject.toml [project] requires-python = "
                                    f'"{detected_python}"',
                                    f'{ci_file}: python-version = "{ci_ver}"',
                                ),
                                summary=(
                                    "version minima de Python en pyproject.toml "
                                    "no coincide con la matriz de CI"
                                ),
                                suggested_resolution=(
                                    "alinear requires-python con la version de CI "
                                    "o actualizar la matriz"
                                ),
                            )
                        )

    return findings, unknowns, conflicts


def _quality_surface(
    repo: ScannedRepository,
    archetype: str,
) -> QualitySurface | None:
    if archetype in ("unknown",):
        return None
    validated: list[str] = []
    if repo.src_layout_dirs:
        for pkg in sorted(repo.src_layout_dirs):
            validated.append(f"src/{pkg}/")
    elif repo.top_level_packages:
        for pkg in sorted(repo.top_level_packages):
            validated.append(f"{pkg}/")
    if repo.has_tests_dir:
        validated.append("tests/")
    excluded: list[str] = []
    for d in sorted(repo.pipeline_dirs):
        excluded.append(f"{d}/")
    for d in sorted(repo.data_dirs):
        excluded.append(f"{d}/")
    if not validated and not excluded:
        return None
    return QualitySurface(
        note="Provisional. No claim of validation.",
        suggested_validated_paths=tuple(sorted(set(validated))),
        suggested_excluded_paths=tuple(sorted(set(excluded))),
    )


def _atomic_write(path: Path, content: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, path)
    except OSError:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        raise


def _build_result(
    target: Path,
    repo: ScannedRepository,
) -> tuple[AuditResult, list[Finding], list[Unknown], list[Conflict]]:
    """Construye el AuditResult desde el ScannedRepository."""
    from python_ai_template.audit.model import (
        Git as GitModel,
    )

    archetype = classify(repo)
    authority = _build_authority(repo)
    tooling = _build_tooling(repo)
    runtimes = _build_runtimes(repo)
    ci = _build_ci(repo)
    integrations = _build_integrations(repo)
    findings, unknowns, conflicts = _build_findings_and_unknowns(
        repo, authority, tooling, list(repo.ci_python_versions)
    )
    quality = _quality_surface(repo, archetype.classification)

    git_model = None
    if repo.git_info is not None:
        git_model = GitModel(
            head=repo.git_info.get("head", ""),
            branch=repo.git_info.get("branch", ""),
            porcelain_clean=bool(repo.git_info.get("porcelain_clean", True)),
            untracked_count=int(repo.git_info.get("untracked_count", 0)),
            modified_count=int(repo.git_info.get("modified_count", 0)),
        )

    audit_result = AuditResult(
        schema_version=1,
        template_version="0.3.3",
        operation="audit",
        repository=Repository(),
        archetype=archetype,
        git=git_model,
        authority=authority,
        detected_runtimes=runtimes,
        detected_tooling=tooling,
        detected_ci=ci,
        detected_integrations=integrations,
        quality_surface_proposed=quality,
        findings=tuple(findings),
        unknowns=tuple(unknowns),
        conflicts=tuple(conflicts),
    )
    return audit_result, findings, unknowns, conflicts


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    target = _validate_target(args.repository)
    if target is None:
        return 2

    output_path = _validate_output(target, args.output)
    if args.output is not None and output_path is None:
        return 2

    started = time.monotonic()
    scanned = scan(target)
    audit_result, _, _, _ = _build_result(target, scanned)
    rendered = render(audit_result)
    duration = time.monotonic() - started

    if output_path is None:
        sys.stdout.write(rendered)
        sys.stdout.flush()
    else:
        try:
            _atomic_write(output_path, rendered)
        except OSError as exc:
            print(
                f"error: no se pudo escribir --output {output_path}: {exc}",
                file=sys.stderr,
            )
            return 1
        print(
            f"audit completed in {duration:.3f}s; manifest escrito en {output_path}",
            file=sys.stderr,
        )

    return 0
