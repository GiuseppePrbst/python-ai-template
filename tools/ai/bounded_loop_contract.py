"""Simulador del contrato ``bounded execution loop``.

Especificación ejecutable reutilizable del contrato anti-runaway-loop.
Este módulo es un SIMULADOR DE CONTRATO, no un watchdog runtime: modela
las reglas de transición, los estados terminales y los límites, pero NO
controla tool calls reales, NO cancela generación del modelo, NO persiste
checkpoints operacionalmente y NO impone enforcement externo del presupuesto.

Solo biblioteca estándar. Sin dependencias. Sin red.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Estados terminales (lista cerrada)
# ---------------------------------------------------------------------------

TERMINAL_COMPLETED = "COMPLETED"
TERMINAL_FAILED = "FAILED"
TERMINAL_BLOCKED = "BLOCKED"
TERMINAL_BLOCKED_LOOP = "BLOCKED_LOOP"
TERMINAL_ESCALATED = "ESCALATED"
TERMINAL_CANCELLED = "CANCELLED"

TERMINAL_STATES: tuple[str, ...] = (
    TERMINAL_COMPLETED,
    TERMINAL_FAILED,
    TERMINAL_BLOCKED,
    TERMINAL_BLOCKED_LOOP,
    TERMINAL_ESCALATED,
    TERMINAL_CANCELLED,
)

# Límites por defecto del contrato.
DEFAULT_STEP_BUDGET = 12
DEFAULT_MAX_RETRIES = 1
DEFAULT_MAX_NO_PROGRESS = 2


# ---------------------------------------------------------------------------
# Tipos del contrato
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StepOutcome:
    """Resultado observable de una iteración.

    Atributos:

    - ``success``: si la acción logró lo que pretendía.
    - ``state_after``: descripción observable del estado del working
      tree tras la acción. Si coincide con el ``state_before``
      anterior (texto normalizado), no aporta evidencia.
    - ``evidence``: evidencia adicional (logs, ids de commit, nombres
      de tests). Si está vacía, no aporta nada nuevo.
    - ``completes_phase``: marca explícita de que el worker declara
      la fase como completada. Solo este flag produce
      ``terminal_status = COMPLETED``.
    """

    success: bool
    state_after: str = ""
    evidence: str = ""
    completes_phase: bool = False

    def is_progress(self, state_before: str) -> bool:
        """Una iteración aporta progreso si introduce evidencia o un
        cambio observable en ``state_after`` respecto al anterior.

        Reglas:

        - ``evidence`` no vacía cuenta como progreso aunque el
          ``state_after`` no cambie.
        - ``state_after`` no vacío y distinto de ``state_before``
          cuenta como progreso aunque ``evidence`` sea vacía.
        - Cualquier otro caso (state vacío o idéntico sin evidencia)
          es no-progress.
        """
        if self.evidence.strip():
            return True
        if not self.state_after.strip():
            return False
        return self.state_after.strip() != state_before.strip()


@dataclass(frozen=True)
class Action:
    """Acción que el worker intenta ejecutar.

    Es inmutable (frozen=True): el fingerprint no puede modificarse
    después de creado.
    """

    name: str
    fingerprint: str
    state_before: str = ""
    expected_state_change: str = ""


@dataclass
class LoopState:
    """Estado mutable del bounded execution loop."""

    task_id: str
    phase_id: str
    step_number: int = 0
    step_budget: int = DEFAULT_STEP_BUDGET
    no_progress_count: int = 0
    retry_count: int = 0
    same_action_count: int = 0
    state_before: str = ""
    terminal_status: str | None = None
    escalation_reason: str | None = None
    fingerprints_seen: tuple[str, ...] = field(default_factory=tuple)
    completed_phases: tuple[str, ...] = field(default_factory=tuple)

    def is_terminal(self) -> bool:
        return self.terminal_status is not None


@dataclass(frozen=True)
class ResourceLimit:
    """Evento genérico de límite de recurso del proveedor.

    No dependiente de ningún proveedor específico (DeepSeek, MiniMax,
    OpenAI, etc.). Modela la señal que un watchdog o runtime externo
    emite cuando se agota la cuota del proveedor.

    Atributos:
        provider: nombre del proveedor (opcional).
        model: nombre del modelo (opcional).
        limit_kind: tipo de límite (token_plan_exhausted, rate_limit, etc.).
        raw_message: mensaje original del proveedor (se sanitiza antes
            de exponer).
        tool_calls_used: número de tool calls consumidas.
        step_number: paso en el que ocurrió el evento.
        checkpoint_available: indica si existe checkpoint para reanudar.
        resumable: indica si la tarea puede reanudarse con otro modelo.
    """

    provider: str | None = None
    model: str | None = None
    limit_kind: str = "token_plan_exhausted"
    raw_message: str = ""
    tool_calls_used: int = 0
    step_number: int = 0
    checkpoint_available: bool = False
    resumable: bool = True


# ---------------------------------------------------------------------------
# Utilería interna
# ---------------------------------------------------------------------------


def sanitize_message(message: str) -> str:
    """Elimina posibles credenciales del mensaje.

    Sustituye valores de claves, tokens y secretos conocidos por ``***``.
    Conserva la etiqueta (``api_key=``) pero elimina el valor.
    """
    import re

    sanitized = re.sub(
        r"(api[_-]?key|token|secret|password|auth)\s*[:=]\s*\S+",
        r"\1=***",
        message,
        flags=re.IGNORECASE,
    )
    return sanitized


def _advance(
    state: LoopState,
    step_number: int,
    same_action_count: int,
    retry_count: int,
    *,
    state_after: str = "",
    fingerprints: tuple[str, ...] = (),
    no_progress_count: int | None = None,
) -> LoopState:
    """Avanza contadores sin fijar terminal."""
    return LoopState(
        task_id=state.task_id,
        phase_id=state.phase_id,
        step_number=step_number,
        step_budget=state.step_budget,
        no_progress_count=(
            no_progress_count
            if no_progress_count is not None
            else state.no_progress_count
        ),
        retry_count=retry_count,
        same_action_count=same_action_count,
        state_before=state_after or state.state_before,
        terminal_status=state.terminal_status,
        escalation_reason=state.escalation_reason,
        fingerprints_seen=state.fingerprints_seen + fingerprints,
        completed_phases=state.completed_phases,
    )


def _set_terminal(
    state: LoopState,
    status: str,
    reason: str | None,
    *,
    completed: bool = False,
) -> LoopState:
    """Devuelve un LoopState con terminal_status y (opcionalmente)
    la fase marcada como completada."""
    return LoopState(
        task_id=state.task_id,
        phase_id=state.phase_id,
        step_number=state.step_number,
        step_budget=state.step_budget,
        no_progress_count=state.no_progress_count,
        retry_count=state.retry_count,
        same_action_count=state.same_action_count,
        state_before=state.state_before,
        terminal_status=status,
        escalation_reason=reason,
        fingerprints_seen=state.fingerprints_seen,
        completed_phases=(
            state.completed_phases + (state.phase_id,)
            if completed
            else state.completed_phases
        ),
    )


# ---------------------------------------------------------------------------
# Núcleo del contrato
# ---------------------------------------------------------------------------


def run_step(
    state: LoopState,
    action: Action,
    outcome: StepOutcome,
) -> LoopState:
    """Aplica una iteración del contrato bounded execution loop.

    Devuelve un nuevo ``LoopState`` con los contadores actualizados y,
    si corresponde, el ``terminal_status`` fijado. No lanza excepción:
    los estados terminales son valores, no errores.

    Las reglas implementadas deben coincidir con
    ``docs/bounded-loop.md``. El orden de evaluación es:

    1. Estado ya terminal: se devuelve tal cual (idempotencia).
    2. Reinicio de fase ya completada: ``BLOCKED_LOOP``.
    3. Presupuesto agotado al entrar (``step_number >= step_budget``):
       ``ESCALATED``.
    4. Fingerprint repetido del último visto:
       a) ``success=True`` -> ``BLOCKED_LOOP`` (comando exitoso
          repetido, prohibido por contrato).
       b) ``success=False`` y se superó el límite de reintentos ->
          ``BLOCKED_LOOP``.
       c) ``success=False`` sin evidencia nueva -> ``BLOCKED_LOOP``
          (mismo diagnóstico repetido).
       d) ``success=False`` con evidencia nueva -> permite el retry.
    5. Fingerprint nuevo: resetea ``retry_count`` y
       ``same_action_count``.
    6. Progreso vs no-progress:
       - sin progreso y ``no_progress_count >= MAX_NO_PROGRESS``
         -> ``BLOCKED_LOOP``.
    7. Avance y verificación final:
       - ``outcome.completes_phase`` -> ``COMPLETED``.
       - presupuesto agotado tras el paso -> ``ESCALATED``.
    """
    # 1) Reinicio de fase ya completada (prioritario sobre idempotencia:
    #    una fase completada no puede reabrirse).
    if state.phase_id in state.completed_phases:
        return _set_terminal(
            state,
            TERMINAL_BLOCKED_LOOP,
            "reinicio de fase completada",
        )

    # 2) Estado ya terminal: idempotente.
    if state.is_terminal():
        return state

    # 3) Presupuesto agotado al iniciar el paso.
    if state.step_number >= state.step_budget:
        return _set_terminal(
            state,
            TERMINAL_ESCALATED,
            "presupuesto agotado",
        )

    step_number = state.step_number + 1

    # 4) Determinación de same_action_count y retry_count.
    same_action_count = state.same_action_count
    retry_count = state.retry_count
    last_seen = state.fingerprints_seen[-1] if state.fingerprints_seen else None
    is_same_fingerprint = last_seen == action.fingerprint

    if is_same_fingerprint:
        same_action_count += 1
        if outcome.success:
            return _set_terminal(
                _advance(state, step_number, same_action_count, retry_count),
                TERMINAL_BLOCKED_LOOP,
                "comando exitoso repetido",
            )
        retry_count += 1
        if retry_count > DEFAULT_MAX_RETRIES:
            return _set_terminal(
                _advance(state, step_number, same_action_count, retry_count),
                TERMINAL_BLOCKED_LOOP,
                "límite de reintentos superado",
            )
        if not outcome.is_progress(state.state_before):
            return _set_terminal(
                _advance(
                    state,
                    step_number,
                    same_action_count,
                    retry_count,
                    no_progress_count=state.no_progress_count + 1,
                ),
                TERMINAL_BLOCKED_LOOP,
                "mismo diagnóstico repetido sin evidencia",
            )
    else:
        same_action_count = 1
        retry_count = 0

    # 5) Progreso vs no-progress.
    progress = outcome.is_progress(state.state_before)
    no_progress_count = 0 if progress else state.no_progress_count + 1
    if not progress and no_progress_count >= DEFAULT_MAX_NO_PROGRESS:
        return _set_terminal(
            _advance(
                state,
                step_number,
                same_action_count,
                retry_count,
                no_progress_count=no_progress_count,
            ),
            TERMINAL_BLOCKED_LOOP,
            "dos iteraciones sin progreso",
        )

    # 6) Avance y verificación final.
    advanced = _advance(
        state,
        step_number,
        same_action_count,
        retry_count,
        state_after=outcome.state_after,
        fingerprints=(action.fingerprint,),
        no_progress_count=no_progress_count,
    )

    if outcome.success and progress and outcome.completes_phase:
        return _set_terminal(advanced, TERMINAL_COMPLETED, None, completed=True)

    if step_number >= state.step_budget:
        return _set_terminal(advanced, TERMINAL_ESCALATED, "presupuesto agotado")

    return advanced


def handle_resource_limit(state: LoopState, event: ResourceLimit) -> LoopState:
    """Procesa un evento de límite de recurso.

    Siempre produce ``ESCALATED`` con el mensaje sanitizado.
    Si el estado ya es terminal, lo devuelve intacto (idempotente).

    Reglas:
    - El ``limit_kind`` se incluye en ``escalation_reason``.
    - El mensaje se sanitiza (no expone credenciales).
    - ``checkpoint_available`` y ``resumable`` se conservan en el evento
      para que el orquestador decida si reanuda.
    """
    if state.is_terminal():
        return state

    sanitized = sanitize_message(event.raw_message)
    reason = f"resource_limit: {event.limit_kind}"
    if event.provider:
        reason += f" provider={event.provider}"
    if sanitized:
        truncated = sanitized[:200]
        reason += f" message={truncated}"

    return LoopState(
        task_id=state.task_id,
        phase_id=state.phase_id,
        step_number=event.step_number or (state.step_number + 1),
        step_budget=state.step_budget,
        no_progress_count=state.no_progress_count,
        retry_count=state.retry_count,
        same_action_count=state.same_action_count,
        state_before=state.state_before,
        terminal_status=TERMINAL_ESCALATED,
        escalation_reason=reason,
        fingerprints_seen=state.fingerprints_seen,
        completed_phases=state.completed_phases,
    )
