"""Renderer TOML determinista y limitado al schema del audit.

No es un serializador TOML generico. Solo emite los tipos concretos
permitidos por el schema (string, int, bool, array de escalares,
tabla, array de tablas) y omite cualquier campo cuyo valor sea
``None`` o una coleccion vacia.

El orden de escritura es estable: claves de tablas ordenadas
alfabeticamente, subtablas ordenadas por nombre de clave, arrays de
tablas ordenados por ``id`` ascendente.

El escape de strings cubre ``\\``, ``"``, ``\n``, ``\t``, ``\r`` y
caracteres de control por debajo de ``0x20`` (via ``\\uXXXX``).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import fields, is_dataclass
from typing import Any, cast

from python_ai_template.audit.model import (
    AuditResult,
)


def _escape_string(s: str) -> str:
    out: list[str] = []
    for ch in s:
        code = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif code < 0x20:
            out.append(f"\\u{code:04x}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


_Scalar = bool | int | str


def _scalar(v: object) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return _escape_string(v)
    raise TypeError(f"unsupported scalar type: {type(v).__name__}")


def _inline_array(v: Sequence[object]) -> str:
    return "[" + ", ".join(_scalar(x) for x in v) + "]"


def _is_empty(v: object) -> bool:
    if v is None:
        return True
    if isinstance(v, (str, tuple, list)):
        return not v
    if isinstance(v, Mapping):
        return not v
    return False


def _as_pairs(obj: object) -> dict[str, Any]:
    """Convierte un dataclass o mapping a un dict ordenado por clave."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: getattr(obj, f.name) for f in fields(obj)}
    if isinstance(obj, Mapping):
        m = cast(Mapping[str, Any], obj)
        return {k: m[k] for k in m}
    raise TypeError(f"cannot convert {type(obj).__name__} to pairs")


def _emit_inline(buf: list[str], key: str, value: object) -> None:
    if _is_empty(value):
        return
    if isinstance(value, (list, tuple)):
        buf.append(f"{key} = {_inline_array(cast(Sequence[object], value))}")
    else:
        buf.append(f"{key} = {_scalar(value)}")


def _emit_table(buf: list[str], name: str, obj: Any) -> None:
    pairs = _as_pairs(obj)
    if all(_is_empty(pairs[k]) for k in pairs):
        return
    buf.append(f"[{name}]")
    for k in sorted(pairs.keys()):
        _emit_inline(buf, k, pairs[k])
    buf.append("")


def _emit_subtable(buf: list[str], parent: str, key: str, obj: Any) -> None:
    pairs = _as_pairs(obj)
    if all(_is_empty(pairs[k]) for k in pairs):
        return
    buf.append(f"[{parent}.{key}]")
    for k in sorted(pairs.keys()):
        _emit_inline(buf, k, pairs[k])
    buf.append("")


def _emit_array_of_tables(buf: list[str], name: str, items: Iterable[object]) -> None:
    for item in items:
        pairs = _as_pairs(item)
        buf.append(f"[[{name}]]")
        for k in sorted(pairs.keys()):
            v = pairs[k]
            if _is_empty(v):
                continue
            if isinstance(v, (list, tuple)):
                buf.append(f"{k} = {_inline_array(cast(Sequence[object], v))}")
            else:
                buf.append(f"{k} = {_scalar(v)}")
        buf.append("")


def render(result: AuditResult) -> str:
    """Renderiza un :class:`AuditResult` a TOML determinista."""
    buf: list[str] = []
    buf.append(f"schema_version = {result.schema_version}")
    buf.append(f'template_version = "{result.template_version}"')
    buf.append(f'operation = "{result.operation}"')
    buf.append("")

    _emit_table(buf, "repository", result.repository)

    if result.git is not None:
        _emit_table(buf, "git", result.git)

    auth_pairs = _as_pairs(result.authority)
    if any(not _is_empty(auth_pairs[k]) for k in auth_pairs):
        _emit_table(buf, "authority", result.authority)

    _emit_table(buf, "archetype", result.archetype)

    for key in sorted(result.detected_runtimes.keys()):
        _emit_subtable(buf, "detected_runtimes", key, result.detected_runtimes[key])

    tooling_pairs = _as_pairs(result.detected_tooling)
    if any(not _is_empty(tooling_pairs[k]) for k in tooling_pairs):
        _emit_table(buf, "detected_tooling", result.detected_tooling)

    for key in sorted(result.detected_ci.keys()):
        _emit_subtable(buf, "detected_ci", key, result.detected_ci[key])

    for key in sorted(result.detected_integrations.keys()):
        integration = result.detected_integrations[key]
        if not _is_empty(integration.evidence):
            _emit_subtable(buf, "detected_integrations", key, integration)

    if result.quality_surface_proposed is not None:
        _emit_table(buf, "quality_surface_proposed", result.quality_surface_proposed)

    if result.findings:
        sorted_findings = sorted(result.findings, key=lambda f: f.id)
        _emit_array_of_tables(buf, "findings", sorted_findings)

    if result.unknowns:
        sorted_unknowns = sorted(result.unknowns, key=lambda u: u.id)
        _emit_array_of_tables(buf, "unknowns", sorted_unknowns)

    if result.conflicts:
        sorted_conflicts = sorted(result.conflicts, key=lambda c: c.id)
        _emit_array_of_tables(buf, "conflicts", sorted_conflicts)

    return "\n".join(buf) + "\n"
