"""Tests hermeticos de los fixtures de compactacion (v0.3.3).

Cubre ``.opencode/fixtures/compaction-checkpoint.md`` y
``.opencode/fixtures/compaction-filler.md``.

Los tests son completamente hermeticos: solo leen archivos del
repositorio, no ejecutan ``uv``, ``subprocess``, ``build``,
``wheel`` ni red. La validacion del build real se hace fuera de
pytest con::

    rm -rf dist
    uv build
    uv run python tools/ai/verify_wheel.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

CHECKPOINT_PATH = REPO_ROOT / ".opencode" / "fixtures" / "compaction-checkpoint.md"
FILLER_PATH = REPO_ROOT / ".opencode" / "fixtures" / "compaction-filler.md"

CANONICAL_HEADINGS: tuple[str, ...] = (
    "Objetivo actual",
    "Estado de la tarea",
    "Hechos verificados",
    "Decisiones adoptadas",
    "Archivos modificados",
    "Validaciones ejecutadas",
    "Errores pendientes",
    "Enfoques rechazados y motivo",
    "Divergencias detectadas",
    "Siguiente acción concreta",
)

CANONICAL_MARKERS: tuple[str, ...] = (
    "OBJECTIVE-01",
    "STATE-01",
    "FACT-01",
    "FACT-02",
    "DECISION-01",
    "FILE-01",
    "VALIDATION-01",
    "ERROR-01",
    "REJECTED-01",
    "DIVERGENCE-01",
    "NEXT-01",
)

# Terminos prohibidos en el filler (ingles y espanol). Se buscan como
# subcadenas case-insensitive para detectar plurales y variantes.
FORBIDDEN_FILLER_TERMS: tuple[str, ...] = (
    "objective",
    "decision",
    "validation",
    "error",
    "next action",
    "file modified",
    "objetivo",
    "decisión",
    "validación",
    "siguiente acción",
    "archivo modificado",
)

# Patrones evidentes de secretos a evitar en ambos fixtures.
SECRET_PATTERNS: tuple[str, ...] = (
    "-----BEGIN",
    "api_key=",
    "token=",
    "password=",
    "secret=",
)

# Patrones de URLs.
URL_PATTERNS: tuple[str, ...] = (
    "http://",
    "https://",
)

# Patrones de rutas personales.
PERSONAL_PATH_PATTERNS: tuple[str, ...] = (
    "/home/",
    "~/",
    "C:\\Users",
)

# Referencias al proyecto real que el fixture no debe contener.
REAL_PROJECT_REFERENCES: tuple[str, ...] = (
    "python-ai-template",
    "v0.3.3",
    "structured-compaction",
    "~/.config/opencode",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"fixture ausente: {path}"
    return path.read_text(encoding="utf-8")


def _extract_h2(text: str) -> list[str]:
    return re.findall(r"^## (.+)$", text, flags=re.MULTILINE)


def _extract_section(text: str, marker: str) -> str:
    """Extrae el texto asociado a un marcador hasta el siguiente marcador.

    Si el marcador no aparece, devuelve cadena vacia.
    """
    if marker not in text:
        return ""
    start = text.index(marker)
    rest = text[start + len(marker) :]
    # Buscar el siguiente marcador canonico
    next_positions: list[int] = []
    for m in CANONICAL_MARKERS:
        if m == marker:
            continue
        idx = rest.find(m)
        if idx != -1:
            next_positions.append(idx)
    end: int = min(next_positions) if next_positions else len(rest)
    return rest[:end].strip()


# ---------------------------------------------------------------------------
# Checkpoint: headings y marcadores
# ---------------------------------------------------------------------------


def test_checkpoint_has_ten_headings_in_order() -> None:
    """Los 10 headings canonicos aparecen exactamente una vez y en orden."""
    text = _read(CHECKPOINT_PATH)
    headings = _extract_h2(text)
    assert headings == list(CANONICAL_HEADINGS), (
        f"headings del checkpoint no coinciden con los 10 canonicos: {headings}"
    )


def test_checkpoint_each_marker_appears_exactly_once() -> None:
    """Cada uno de los 11 marcadores aparece exactamente una vez."""
    text = _read(CHECKPOINT_PATH)
    for marker in CANONICAL_MARKERS:
        count = text.count(marker)
        assert count == 1, f"marcador {marker!r} aparece {count} veces; se esperaba 1"


def test_checkpoint_file01_declares_no_real_file() -> None:
    """FILE-01 declara que no se creo ningun archivo real."""
    text = _read(CHECKPOINT_PATH)
    section = _extract_section(text, "FILE-01")
    assert section, "seccion FILE-01 ausente"
    lowered = section.lower()
    # La declaracion debe negar la creacion de archivos reales.
    has_negation = (
        "ninguno" in lowered
        or "ningún" in lowered
        or "no modifica" in lowered
        or "no se ha" in lowered
        or "no se han" in lowered
        or "no se creo" in lowered
        or "no se creó" in lowered
        or "declarativo" in lowered
    )
    assert has_negation, (
        f"FILE-01 no declara que no se haya creado ningun archivo real: {section!r}"
    )


# ---------------------------------------------------------------------------
# Filler: pureza y ausencia de estado
# ---------------------------------------------------------------------------


def test_filler_has_no_markers() -> None:
    """El filler no contiene ninguno de los 11 marcadores."""
    text = _read(FILLER_PATH)
    for marker in CANONICAL_MARKERS:
        assert marker not in text, f"el filler contiene el marcador {marker!r}"


def test_filler_no_state_terms() -> None:
    """El filler no contiene terminos de estado del checkpoint."""
    text = _read(FILLER_PATH)
    lowered = text.lower()
    for term in FORBIDDEN_FILLER_TERMS:
        assert term not in lowered, f"el filler contiene el termino prohibido {term!r}"


# ---------------------------------------------------------------------------
# Ausencia de secretos, URLs, rutas personales y referencias reales
# ---------------------------------------------------------------------------


def test_fixtures_have_no_obvious_secrets() -> None:
    """Ningun fixture contiene patrones evidentes de secretos."""
    for path in (CHECKPOINT_PATH, FILLER_PATH):
        text = _read(path)
        lowered = text.lower()
        for pattern in SECRET_PATTERNS:
            assert pattern.lower() not in lowered, (
                f"{path.name} contiene patron de secreto {pattern!r}"
            )


def test_fixtures_no_urls() -> None:
    """Ningun fixture contiene URLs http:// o https://."""
    for path in (CHECKPOINT_PATH, FILLER_PATH):
        text = _read(path)
        for pattern in URL_PATTERNS:
            assert pattern not in text, f"{path.name} contiene URL {pattern!r}"


def test_fixtures_no_personal_paths() -> None:
    """Ningun fixture contiene rutas personales (/home/, ~/, C:\\Users)."""
    for path in (CHECKPOINT_PATH, FILLER_PATH):
        text = _read(path)
        for pattern in PERSONAL_PATH_PATTERNS:
            assert pattern not in text, (
                f"{path.name} contiene ruta personal {pattern!r}"
            )


def test_fixtures_no_real_project_references() -> None:
    """Ningun fixture menciona el proyecto real ni su configuracion global."""
    for path in (CHECKPOINT_PATH, FILLER_PATH):
        text = _read(path)
        for reference in REAL_PROJECT_REFERENCES:
            assert reference not in text, (
                f"{path.name} contiene referencia al proyecto real {reference!r}"
            )


# ---------------------------------------------------------------------------
# Sincronizacion root <-> template
# ---------------------------------------------------------------------------


def test_checkpoint_root_template_sync() -> None:
    """El checkpoint de la raiz es byte a byte identico al del template."""
    template = (
        REPO_ROOT
        / "src"
        / "python_ai_template"
        / "template"
        / ".opencode"
        / "fixtures"
        / "compaction-checkpoint.md"
    )
    assert template.is_file(), f"template ausente: {template}"
    assert CHECKPOINT_PATH.read_bytes() == template.read_bytes(), (
        "el checkpoint de la raiz difiere del template canonico"
    )


def test_filler_root_template_sync() -> None:
    """El filler de la raiz es byte a byte identico al del template."""
    template = (
        REPO_ROOT
        / "src"
        / "python_ai_template"
        / "template"
        / ".opencode"
        / "fixtures"
        / "compaction-filler.md"
    )
    assert template.is_file(), f"template ausente: {template}"
    assert FILLER_PATH.read_bytes() == template.read_bytes(), (
        "el filler de la raiz difiere del template canonico"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
