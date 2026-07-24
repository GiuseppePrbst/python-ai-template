"""Tests del registrador de evaluaciones (``record_evaluation.py``).

Tests hermeticos: usan ``tmp_path`` y nunca dependen del repositorio
real. Validan preview, escritura atomica, validacion de campos,
limites de longitud y conservacion del contenido previo.
"""

from __future__ import annotations

import datetime as _dt
import re
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "tools" / "ai"),
)

import record_evaluation as rec  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "tools" / "ai" / "record_evaluation.py"


def _fixed_today() -> _dt.date:
    return _dt.date(2026, 7, 23)


def _good_args() -> dict[str, object]:
    return {
        "task": "Probar el gate estatico de OpenCode",
        "agent": "scout",
        "model": "modelo-x",
        "provider": "proveedor-y",
        "result": "approved",
        "duration_minutes": 12.5,
        "corrections": "ninguna",
        "escalated": False,
        "notes": "todo OK",
    }


def _build_eval(**overrides: object) -> rec.Evaluation:
    args = _good_args()
    args.update(overrides)
    return rec.Evaluation(**args)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Validacion
# ---------------------------------------------------------------------------


def test_required_args_missing() -> None:
    rc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--task",
            "x",
            # falta --agent
            "--model",
            "m",
            "--provider",
            "p",
            "--result",
            "approved",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert rc.returncode != 0


def test_result_invalid() -> None:
    with pytest.raises(rec.EvaluationError):
        rec.validate(_build_eval(result="invalid-value"))


def test_duration_negative() -> None:
    with pytest.raises(rec.EvaluationError):
        rec.validate(_build_eval(duration_minutes=-1.0))


def test_duration_nan() -> None:
    with pytest.raises(rec.EvaluationError):
        rec.validate(_build_eval(duration_minutes=float("nan")))


def test_duration_infinite() -> None:
    with pytest.raises(rec.EvaluationError):
        rec.validate(_build_eval(duration_minutes=float("inf")))


def test_duration_absent_is_ok() -> None:
    rec.validate(_build_eval(duration_minutes=None))


def test_duration_zero_is_ok() -> None:
    rec.validate(_build_eval(duration_minutes=0.0))


def test_duration_decimal_is_ok() -> None:
    rec.validate(_build_eval(duration_minutes=2.75))


def test_duration_large_value_is_ok() -> None:
    rec.validate(_build_eval(duration_minutes=99999.0))


def test_escalated_invalid_value() -> None:
    rc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--task",
            "x",
            "--agent",
            "a",
            "--model",
            "m",
            "--provider",
            "p",
            "--result",
            "approved",
            "--escalated",
            "maybe",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert rc.returncode != 0


def test_control_chars_rejected() -> None:
    with pytest.raises(rec.EvaluationError):
        rec.validate(_build_eval(task="hola\x00mundo"))


def test_pem_block_rejected() -> None:
    with pytest.raises(rec.EvaluationError):
        rec.validate(
            _build_eval(
                corrections=(
                    "-----BEGIN PRIVATE KEY-----\nABC\n-----END PRIVATE KEY-----"
                )
            )
        )


def test_length_limit_task() -> None:
    long_task = "x" * 201
    with pytest.raises(rec.EvaluationError):
        rec.validate(_build_eval(task=long_task))


def test_length_limit_notes() -> None:
    long_notes = "x" * 2001
    with pytest.raises(rec.EvaluationError):
        rec.validate(_build_eval(notes=long_notes))


def test_multiline_in_single_line_rejected() -> None:
    with pytest.raises(rec.EvaluationError):
        rec.validate(_build_eval(agent="line1\nline2"))


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def test_build_entry_duration_absent() -> None:
    entry = rec.build_entry(_build_eval(duration_minutes=None), _fixed_today())
    assert "no registrada" in entry


def test_build_entry_duration_present() -> None:
    entry = rec.build_entry(_build_eval(duration_minutes=30.0), _fixed_today())
    assert "30.0 minutos" in entry
    assert "no registrada" not in entry


def test_build_entry_escalated_yes() -> None:
    entry = rec.build_entry(_build_eval(escalated=True), _fixed_today())
    assert "**Escalado**: sí." in entry


def test_build_entry_escalated_no() -> None:
    entry = rec.build_entry(_build_eval(escalated=False), _fixed_today())
    assert "**Escalado**: no." in entry


def test_build_entry_date_format() -> None:
    entry = rec.build_entry(_build_eval(), _fixed_today())
    assert entry.startswith("### 2026-07-23 — ")


# ---------------------------------------------------------------------------
# Escritura atomica
# ---------------------------------------------------------------------------


def test_append_entry_creates_with_header(tmp_path: Path) -> None:
    output = tmp_path / "evals.md"
    rec.append_entry(output, rec.build_entry(_build_eval(), _fixed_today()))
    assert output.is_file()
    content = output.read_text(encoding="utf-8")
    assert content.startswith("# Evaluaciones de modelos\n")
    assert "---" in content
    assert "### 2026-07-23" in content
    assert not (tmp_path / "evals.md.tmp").exists()


def test_append_entry_preserves_previous(tmp_path: Path) -> None:
    output = tmp_path / "evals.md"
    output.write_text(
        "# Evaluaciones de modelos\n\nIntro.\n\n---\n\n"
        "### 2026-01-01 — Previa\n\n- contenido previo\n\n",
        encoding="utf-8",
    )
    rec.append_entry(output, rec.build_entry(_build_eval(), _fixed_today()))
    content = output.read_text(encoding="utf-8")
    assert "2026-01-01 — Previa" in content
    assert "contenido previo" in content
    assert "2026-07-23" in content
    assert not (tmp_path / "evals.md.tmp").exists()


def test_append_entry_atomic_no_tmp_left(tmp_path: Path) -> None:
    output = tmp_path / "evals.md"
    rec.append_entry(output, rec.build_entry(_build_eval(), _fixed_today()))
    rec.append_entry(output, rec.build_entry(_build_eval(), _fixed_today()))
    assert not (tmp_path / "evals.md.tmp").exists()
    content = output.read_text(encoding="utf-8")
    assert content.count("### 2026-07-23") == 2


def test_append_entry_parent_dir_missing() -> None:
    bad = Path("/tmp/this-dir-must-not-exist-xyz-789/evals.md")
    if bad.parent.exists():
        pytest.skip("el directorio existe por casualidad; saltando")
    with pytest.raises(rec.EvaluationError):
        rec.append_entry(bad, "### 2026-07-23 — x\n\n")


def test_append_entry_preserves_utf8(tmp_path: Path) -> None:
    output = tmp_path / "evals.md"
    eval_data = _build_eval(task="Tarea con tildes: compactación y ñ")
    rec.append_entry(output, rec.build_entry(eval_data, _fixed_today()))
    content = output.read_text(encoding="utf-8")
    assert "compactación" in content
    assert "ñ" in content


# ---------------------------------------------------------------------------
# Limpieza de .tmp ante fallo o interrupcion
# ---------------------------------------------------------------------------


def test_append_entry_cleans_tmp_on_failure(tmp_path: Path) -> None:
    """Si replace() falla, el .tmp se elimina y el original permanece."""
    output = tmp_path / "evals.md"
    output.write_text("previous content\n", encoding="utf-8")

    with mock.patch.object(Path, "replace", side_effect=OSError("simulated failure")):
        with pytest.raises(OSError, match="simulated failure"):
            rec.append_entry(output, rec.build_entry(_build_eval(), _fixed_today()))

    assert output.read_text(encoding="utf-8") == "previous content\n"
    assert not (tmp_path / "evals.md.tmp").exists()


def test_append_entry_cleans_tmp_on_keyboard_interrupt(tmp_path: Path) -> None:
    """Si KeyboardInterrupt ocurre entre write_text y replace,
    el .tmp se elimina, el original permanece y la excepcion se propaga."""
    output = tmp_path / "evals.md"
    output.write_text("previous content\n", encoding="utf-8")

    with mock.patch.object(Path, "replace", side_effect=KeyboardInterrupt()):
        with pytest.raises(KeyboardInterrupt):
            rec.append_entry(output, rec.build_entry(_build_eval(), _fixed_today()))

    assert output.read_text(encoding="utf-8") == "previous content\n"
    assert not (tmp_path / "evals.md.tmp").exists()


# ---------------------------------------------------------------------------
# CLI: preview vs escritura
# ---------------------------------------------------------------------------


def test_cli_preview_does_not_write(tmp_path: Path) -> None:
    output = tmp_path / "evals.md"
    rc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--task",
            "tarea X",
            "--agent",
            "scout",
            "--model",
            "m",
            "--provider",
            "p",
            "--result",
            "approved",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert rc.returncode == 0
    assert "--- PREVIEW ---" in rc.stdout
    assert "--- END PREVIEW ---" in rc.stdout
    assert not output.exists()


def test_cli_write_appends(tmp_path: Path) -> None:
    output = tmp_path / "evals.md"
    rc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--task",
            "tarea X",
            "--agent",
            "scout",
            "--model",
            "m",
            "--provider",
            "p",
            "--result",
            "approved",
            "--output",
            str(output),
            "--write",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert rc.returncode == 0, rc.stderr
    assert output.is_file()
    content = output.read_text(encoding="utf-8")
    assert "tarea X" in content
    # Solo una entrada
    matches = re.findall(r"^### \d{4}-\d{2}-\d{2}", content, flags=re.MULTILINE)
    assert len(matches) == 1


def test_cli_output_dir_missing(tmp_path: Path) -> None:
    bad = tmp_path / "nope" / "evals.md"
    rc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--task",
            "tarea",
            "--agent",
            "scout",
            "--model",
            "m",
            "--provider",
            "p",
            "--result",
            "approved",
            "--output",
            str(bad),
            "--write",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert rc.returncode != 0


def test_cli_default_output() -> None:
    """El default es docs/ai/evaluations.md (no se ejecuta contra el repo)."""
    args = rec.parse_args(
        [
            "--task",
            "x",
            "--agent",
            "a",
            "--model",
            "m",
            "--provider",
            "p",
            "--result",
            "approved",
        ]
    )
    assert args.output == "docs/ai/evaluations.md"
    assert args.escalated == "no"
    assert args.duration_minutes is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
