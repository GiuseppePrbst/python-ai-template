"""Tests del contrato ``bounded execution loop``.

Importa la especificación ejecutable desde ``tools/ai/bounded_loop_contract.py``
y verifica los 8 escenarios operativos, invariantes, y ResourceLimit.

No forma parte del paquete distribuible: el runtime real debe ser un
watchdog externo (ver sección "Frontera explícita" del contrato).

Solo biblioteca estándar. Sin dependencias. Sin red.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.ai.bounded_loop_contract import (  # noqa: E402
    DEFAULT_MAX_NO_PROGRESS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_STEP_BUDGET,
    TERMINAL_BLOCKED,
    TERMINAL_BLOCKED_LOOP,
    TERMINAL_CANCELLED,
    TERMINAL_COMPLETED,
    TERMINAL_ESCALATED,
    TERMINAL_FAILED,
    TERMINAL_STATES,
    Action,
    LoopState,
    ResourceLimit,
    StepOutcome,
    handle_resource_limit,
    run_step,
    sanitize_message,
)


def _start(
    task_id: str,
    phase_id: str,
    step_budget: int = DEFAULT_STEP_BUDGET,
) -> LoopState:
    return LoopState(task_id=task_id, phase_id=phase_id, step_budget=step_budget)


def _ok(state_after: str = "ok") -> StepOutcome:
    return StepOutcome(success=True, state_after=state_after, evidence="ok")


def _fail(state_after: str = "") -> StepOutcome:
    return StepOutcome(success=False, state_after=state_after, evidence="")


# ---------------------------------------------------------------------------
# Escenarios exigidos por la unidad anti-runaway-loop
# ---------------------------------------------------------------------------


def test_scenario_1_same_command_repeated_blocked_loop() -> None:
    """Mismo comando repetido: termina en BLOCKED_LOOP."""
    state = _start("audit", "fix-defect")
    state = run_step(
        state,
        Action(name="test", fingerprint="F1"),
        _ok(),
    )
    assert state.terminal_status is None
    next_state = run_step(
        state,
        Action(name="test", fingerprint="F1"),
        _ok(),
    )
    assert next_state.terminal_status == TERMINAL_BLOCKED_LOOP
    assert "exitoso repetido" in (next_state.escalation_reason or "")


def test_scenario_2_same_diagnosis_text_repeated_blocked_loop() -> None:
    """Mismo diagnostico textual repetido sin evidencia nueva:
    termina en BLOCKED_LOOP."""
    state = _start("audit", "diagnose")
    state = run_step(
        state,
        Action(name="read", fingerprint="D1"),
        StepOutcome(success=True, state_after="defecto X", evidence="log1"),
    )
    assert state.terminal_status is None
    # Mismo fingerprint, mismo state_after, sin evidencia nueva.
    next_state = run_step(
        state,
        Action(name="read", fingerprint="D1"),
        StepOutcome(success=False, state_after="defecto X", evidence=""),
    )
    assert next_state.terminal_status == TERMINAL_BLOCKED_LOOP


def test_scenario_3_failure_correction_distinct_test_allowed() -> None:
    """Fallo, correccion con fingerprint distinto y prueba distinta:
    permitido y completa la fase."""
    state = _start("audit", "fix-and-test")
    state = run_step(
        state,
        Action(name="compile", fingerprint="C1"),
        _fail(),
    )
    assert state.terminal_status is None
    state = run_step(
        state,
        Action(name="edit", fingerprint="E1", expected_state_change="fixed"),
        StepOutcome(success=True, state_after="fixed", evidence="patch"),
    )
    assert state.terminal_status is None
    final = run_step(
        state,
        Action(name="test", fingerprint="T1", expected_state_change="fixed"),
        StepOutcome(
            success=True,
            state_after="fixed",
            evidence="all-pass",
            completes_phase=True,
        ),
    )
    assert final.terminal_status == TERMINAL_COMPLETED


def test_scenario_4_successful_command_repeated_blocked() -> None:
    """Comando exitoso repetido: bloqueado aunque tenga exito."""
    state = _start("audit", "verify")
    state = run_step(
        state,
        Action(name="verify", fingerprint="V1"),
        _ok("passed"),
    )
    assert state.terminal_status is None
    next_state = run_step(
        state,
        Action(name="verify", fingerprint="V1"),
        _ok("passed"),
    )
    assert next_state.terminal_status == TERMINAL_BLOCKED_LOOP
    assert "exitoso repetido" in (next_state.escalation_reason or "")


def test_scenario_5_two_iterations_no_state_change_blocked_loop() -> None:
    """Dos iteraciones sin cambio de estado: BLOCKED_LOOP."""
    state = _start("audit", "fix-attempt")
    state = run_step(
        state,
        Action(name="read", fingerprint="R1"),
        StepOutcome(success=False, state_after="", evidence=""),
    )
    assert state.no_progress_count == 1
    assert state.terminal_status is None
    next_state = run_step(
        state,
        Action(name="read", fingerprint="R2"),
        StepOutcome(success=False, state_after="", evidence=""),
    )
    assert next_state.terminal_status == TERMINAL_BLOCKED_LOOP
    assert "sin progreso" in (next_state.escalation_reason or "")


def test_scenario_6_real_progress_between_iterations_allowed() -> None:
    """Progreso real entre iteraciones: permitido y avanza."""
    state = _start("audit", "iterate")
    state = run_step(
        state,
        Action(name="edit", fingerprint="E1"),
        StepOutcome(success=True, state_after="change1", evidence="diff"),
    )
    assert state.terminal_status is None
    next_state = run_step(
        state,
        Action(name="test", fingerprint="T1"),
        StepOutcome(success=True, state_after="change2", evidence="green"),
    )
    assert next_state.terminal_status is None
    assert next_state.no_progress_count == 0


def test_scenario_7_budget_exhausted_escalated() -> None:
    """Presupuesto agotado: ESCALATED al final del ultimo paso."""
    state = _start("audit", "long-fix", step_budget=3)
    state = run_step(
        state,
        Action(name="edit", fingerprint="E1"),
        StepOutcome(success=True, state_after="v1", evidence="d1"),
    )
    assert state.terminal_status is None
    state = run_step(
        state,
        Action(name="edit", fingerprint="E2"),
        StepOutcome(success=True, state_after="v2", evidence="d2"),
    )
    assert state.terminal_status is None
    final = run_step(
        state,
        Action(name="edit", fingerprint="E3"),
        StepOutcome(success=True, state_after="v3", evidence="d3"),
    )
    assert final.terminal_status == TERMINAL_ESCALATED
    assert "presupuesto" in (final.escalation_reason or "")


def test_scenario_8_restart_completed_phase_blocked() -> None:
    """Reinicio de fase ya completada: bloqueado por contrato."""
    state = _start("audit", "phase-A")
    state = run_step(
        state,
        Action(name="do", fingerprint="A1"),
        StepOutcome(
            success=True,
            state_after="done",
            evidence="ok",
            completes_phase=True,
        ),
    )
    assert state.terminal_status == TERMINAL_COMPLETED
    next_state = run_step(
        state,
        Action(name="do-again", fingerprint="A2"),
        _ok("done"),
    )
    assert next_state.terminal_status == TERMINAL_BLOCKED_LOOP
    assert "reinicio" in (next_state.escalation_reason or "")


# ---------------------------------------------------------------------------
# Tests auxiliares: invariantes y limites
# ---------------------------------------------------------------------------


def test_terminal_states_are_closed_set() -> None:
    """La lista de estados terminales es la declarada por el contrato."""
    expected = {
        TERMINAL_COMPLETED,
        TERMINAL_FAILED,
        TERMINAL_BLOCKED,
        TERMINAL_BLOCKED_LOOP,
        TERMINAL_ESCALATED,
        TERMINAL_CANCELLED,
    }
    assert set(TERMINAL_STATES) == expected


def test_one_retry_of_same_fingerprint_allowed() -> None:
    """Un retry del mismo fingerprint esta permitido si aporta evidencia
    nueva; el segundo intento del mismo fingerprint, bloqueado."""
    state = _start("audit", "retry")
    state = run_step(
        state,
        Action(name="retry-target", fingerprint="R"),
        _fail(),
    )
    assert state.terminal_status is None
    # Primer retry: falla con evidencia nueva (evidencia "logs").
    state = run_step(
        state,
        Action(name="retry-target", fingerprint="R"),
        StepOutcome(success=False, state_after="x", evidence="logs"),
    )
    assert state.terminal_status is None
    # Segundo intento del mismo fingerprint: bloqueado por "limite de
    # reintentos".
    final = run_step(
        state,
        Action(name="retry-target", fingerprint="R"),
        _fail(),
    )
    assert final.terminal_status == TERMINAL_BLOCKED_LOOP
    assert (
        "reintentos" in (final.escalation_reason or "")
        or "exitoso repetido" in (final.escalation_reason or "")
        or "diagnostico" in (final.escalation_reason or "")
    )


def test_evidence_alone_counts_as_progress() -> None:
    """Si hay evidencia nueva, la iteracion cuenta como progreso aunque
    el ``state_after`` sea identico al anterior."""
    state = _start("audit", "evidence-only")
    state = run_step(
        state,
        Action(name="probe", fingerprint="P1"),
        StepOutcome(success=True, state_after="unchanged", evidence="first"),
    )
    assert state.no_progress_count == 0
    final = run_step(
        state,
        Action(name="probe", fingerprint="P2"),
        StepOutcome(success=True, state_after="unchanged", evidence="second"),
    )
    assert final.no_progress_count == 0
    assert final.terminal_status is None


def test_run_step_is_pure() -> None:
    """run_step no muta su entrada; dos invocaciones con la misma
    entrada producen el mismo resultado."""
    initial = _start("audit", "pure")
    a = run_step(
        initial,
        Action(name="x", fingerprint="X"),
        _ok("ok"),
    )
    b = run_step(
        initial,
        Action(name="x", fingerprint="X"),
        _ok("ok"),
    )
    assert a == b
    assert initial.step_number == 0


def test_action_is_frozen() -> None:
    """Action es inmutable: cualquier asignacion directa falla."""
    action = Action(name="cmd", fingerprint="fp", expected_state_change="ok")
    assert action.name == "cmd"
    assert action.fingerprint == "fp"
    assert action.expected_state_change == "ok"
    raised = False
    try:
        action.fingerprint = "otro"  # type: ignore[misc]
    except Exception:  # noqa: BLE001 - comportamiento contractual
        raised = True
    assert raised


def test_terminal_state_is_idempotent() -> None:
    """Un estado terminal no se modifica con nuevas acciones."""
    state = _start("audit", "stuck")
    state = run_step(
        state,
        Action(name="x", fingerprint="X"),
        StepOutcome(success=False, state_after="", evidence=""),
    )
    state = run_step(
        state,
        Action(name="y", fingerprint="Y"),
        StepOutcome(success=False, state_after="", evidence=""),
    )
    assert state.terminal_status == TERMINAL_BLOCKED_LOOP
    snapshot = state
    later = run_step(
        state,
        Action(name="z", fingerprint="Z"),
        _ok("ok"),
    )
    assert later == snapshot


def test_default_limits_match_contract() -> None:
    """Los limites por defecto son los declarados en el contrato."""
    assert DEFAULT_STEP_BUDGET >= 1
    assert DEFAULT_MAX_RETRIES == 1
    assert DEFAULT_MAX_NO_PROGRESS == 2


# ---------------------------------------------------------------------------
# Escenario 9 y 10: completes_phase
# ---------------------------------------------------------------------------


def test_completes_phase_false_never_completed() -> None:
    """completes_phase=False nunca produce COMPLETED, aunque haya progreso
    y exito."""
    state = _start("audit", "no-complete", step_budget=5)
    state = run_step(
        state,
        Action(name="do", fingerprint="C1"),
        StepOutcome(
            success=True, state_after="v1", evidence="ok", completes_phase=False
        ),
    )
    assert state.terminal_status is None
    assert state.step_number == 1


def test_completes_phase_true_no_progress_not_completed() -> None:
    """completes_phase=True sin progreso no produce COMPLETED."""
    state = _start("audit", "no-progress-complete", step_budget=5)
    state = run_step(
        state,
        Action(name="stuck", fingerprint="S1"),
        StepOutcome(success=True, state_after="", evidence="", completes_phase=True),
    )
    # Sin progreso (state_after vacio, evidence vacio) -> no completado
    assert state.terminal_status is None
    assert state.no_progress_count == 1


# ---------------------------------------------------------------------------
# Tests de ResourceLimit
# ---------------------------------------------------------------------------


def test_resource_limit_token_exhausted_escalated() -> None:
    """Limite de tokens produce ESCALATED."""
    state = _start("audit", "resource-test")
    event = ResourceLimit(
        provider="test-provider",
        model="test-model",
        limit_kind="token_plan_exhausted",
        tool_calls_used=15,
    )
    result = handle_resource_limit(state, event)
    assert result.terminal_status == TERMINAL_ESCALATED
    assert "resource_limit" in (result.escalation_reason or "")
    assert "token_plan_exhausted" in (result.escalation_reason or "")


def test_resource_limit_checkpoint_available() -> None:
    """Checkpoint marcado como disponible en el evento."""
    event = ResourceLimit(checkpoint_available=True)
    assert event.checkpoint_available is True

    event2 = ResourceLimit(checkpoint_available=False)
    assert event2.checkpoint_available is False


def test_resource_limit_no_further_actions() -> None:
    """Estado terminal por resource_limit no permite acciones posteriores."""
    state = _start("audit", "resource-test")
    event = ResourceLimit(limit_kind="token_plan_exhausted")
    result = handle_resource_limit(state, event)
    assert result.is_terminal()
    # Cualquier run_step posterior debe devolver el mismo estado
    later = run_step(
        result,
        Action(name="x", fingerprint="X"),
        StepOutcome(success=True, state_after="x", evidence="x"),
    )
    assert later == result


def test_resource_limit_resumable() -> None:
    """Tarea puede reanudarse desde checkpoint con otro modelo."""
    state = _start("audit", "resource-test")
    state = run_step(
        state,
        Action(name="step1", fingerprint="S1"),
        StepOutcome(success=True, state_after="v1", evidence="ok"),
    )
    event = ResourceLimit(
        provider="test",
        limit_kind="token_plan_exhausted",
        step_number=state.step_number,
        tool_calls_used=15,
        checkpoint_available=True,
        resumable=True,
    )
    result = handle_resource_limit(state, event)
    assert result.terminal_status == TERMINAL_ESCALATED
    assert event.resumable is True
    # El checkpoint permite reconstruir: fingerprints, step_number, etc.
    assert result.step_number >= 1
    assert len(result.fingerprints_seen) >= 1


def test_resource_limit_message_sanitized() -> None:
    """Mensaje del proveedor se sanitiza y no expone credenciales."""
    raw = "Token limit exceeded. api_key=sk-1234567890abcdef secret=mysecret"
    sanitized = sanitize_message(raw)
    assert "sk-1234567890abcdef" not in sanitized
    assert "mysecret" not in sanitized
    assert "api_key" in sanitized  # La etiqueta se conserva
    assert "=***" in sanitized  # El valor se reemplaza


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
