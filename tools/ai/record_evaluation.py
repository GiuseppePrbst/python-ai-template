"""Registrador manual de evaluaciones para ``python-ai-template``.

CLI opt-in que añade una entrada al registro canonico de
``docs/ai/evaluations.md`` sin usar la red, sin generar IDs de sesion,
sin metricas de tokens y sin timestamps precisos.

Medidas reales anti secreto (no se afirma que los limites "detectan"
secretos; lo que se hace es reducir la superficie de error):

- No existe ``--prompt`` (se omite a proposito).
- Limites de longitud para evitar blobs extensos.
- Rechazo de caracteres de control (excepto ``\\n`` y ``\\t``).
- Advertencia explicita: no introduzca secretos.
- Rechazo de bloques PEM obvios (``-----BEGIN`` ... ``-----END``).

La escritura con ``--write`` es atomica: se escribe a un archivo
temporal en el mismo directorio y luego se hace ``Path.replace()``.

Uso::

    uv run python tools/ai/record_evaluation.py \\
        --task "..." --agent scout --model X --provider Y \\
        --result approved \\
        [--duration-minutes 12.5] [--escalated yes] \\
        [--corrections "..."] [--notes "..."] \\
        [--output docs/ai/evaluations.md] [--write]

Sin ``--write`` imprime la entrada a ``stdout`` y no toca el disco.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Limites de longitud
MAX_TASK_CHARS = 200
MAX_SHORT_CHARS = 100  # agent, model, provider
MAX_TEXT_CHARS = 2000  # corrections, notes

# Resultados validos
VALID_RESULTS = frozenset(
    {
        "approved",
        "approved-with-minor-changes",
        "changes-required",
        "failed",
        "inconclusive",
    }
)

VALID_ESCALATED = frozenset({"yes", "no"})

# Bloque PEM evidente: BEGIN ... END en cualquier parte
PEM_PATTERN = re.compile(r"-----BEGIN [^-]+-----.*?-----END [^-]+-----", re.DOTALL)

# Caracteres de control (excluimos \n y \t que son los unicos utiles)
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


@dataclass(frozen=True)
class Evaluation:
    """Datos validados de una entrada de evaluacion."""

    task: str
    agent: str
    model: str
    provider: str
    result: str
    duration_minutes: float | None
    corrections: str
    escalated: bool
    notes: str


class EvaluationError(ValueError):
    """Error de validacion de la entrada."""


# ---------------------------------------------------------------------------
# Validacion
# ---------------------------------------------------------------------------


def _reject_control_chars(label: str, value: str) -> None:
    if _CONTROL_CHARS.search(value):
        raise EvaluationError(f"{label}: contiene caracteres de control no permitidos")


def _check_single_line(label: str, value: str, limit: int) -> None:
    _reject_control_chars(label, value)
    if "\n" in value or "\r" in value:
        raise EvaluationError(f"{label}: debe ser una sola linea")
    if len(value) > limit:
        raise EvaluationError(
            f"{label}: excede el limite de {limit} caracteres (tiene {len(value)})"
        )


def _check_text(label: str, value: str, limit: int) -> None:
    _reject_control_chars(label, value)
    if len(value) > limit:
        raise EvaluationError(
            f"{label}: excede el limite de {limit} caracteres (tiene {len(value)})"
        )


def _check_pem(label: str, value: str) -> None:
    if PEM_PATTERN.search(value):
        raise EvaluationError(
            f"{label}: contiene un bloque PEM evidente; no introduzca secretos"
        )


def validate(data: Evaluation) -> None:
    """Valida todos los campos de ``data``. Lanza ``EvaluationError`` si falla."""
    _check_single_line("task", data.task, MAX_TASK_CHARS)
    _check_single_line("agent", data.agent, MAX_SHORT_CHARS)
    _check_single_line("model", data.model, MAX_SHORT_CHARS)
    _check_single_line("provider", data.provider, MAX_SHORT_CHARS)
    if data.result not in VALID_RESULTS:
        raise EvaluationError(
            f"result: valor invalido {data.result!r}; valores "
            f"validos: {sorted(VALID_RESULTS)}"
        )
    if data.duration_minutes is not None:
        if (
            not isinstance(data.duration_minutes, float)
            or math.isnan(data.duration_minutes)
            or math.isinf(data.duration_minutes)
        ):
            raise EvaluationError(
                "duration-minutes: debe ser un numero finito (no NaN ni infinito)"
            )
        if data.duration_minutes < 0:
            raise EvaluationError(
                f"duration-minutes: debe ser >= 0 (recibido {data.duration_minutes})"
            )
    _check_text("corrections", data.corrections, MAX_TEXT_CHARS)
    _check_text("notes", data.notes, MAX_TEXT_CHARS)
    _check_pem("task", data.task)
    _check_pem("agent", data.agent)
    _check_pem("model", data.model)
    _check_pem("provider", data.provider)
    _check_pem("corrections", data.corrections)
    _check_pem("notes", data.notes)


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def build_entry(data: Evaluation, today: _dt.date) -> str:
    """Construye la entrada Markdown para ``data``.

    ``today`` se inyecta para que los tests sean deterministas.
    """
    title_task = data.task.splitlines()[0][:60]
    header = f"### {today.isoformat()} — {title_task}"

    if data.duration_minutes is None:
        duration_line = "- **Duración aproximada**: no registrada."
    else:
        duration_line = f"- **Duración**: {data.duration_minutes} minutos."

    escalated_line = "- **Escalado**: sí." if data.escalated else "- **Escalado**: no."

    corrections_text = data.corrections.strip() or "ninguna"
    notes_text = data.notes.strip() or "ninguna"

    lines = [
        header,
        "",
        f"- **Modelo**: `{data.model}`.",
        f"- **Proveedor**: `{data.provider}`.",
        f"- **Agente**: `{data.agent}`.",
        f"- **Tarea**: {data.task}.",
        f"- **Resultado**: `{data.result}`.",
        duration_line,
        escalated_line,
        f"- **Correcciones**: {corrections_text}",
        f"- **Notas**: {notes_text}",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Escritura atomica
# ---------------------------------------------------------------------------


HEADER_BLOCK = (
    "# Evaluaciones de modelos\n"
    "\n"
    "Registro de evaluaciones concretas de modelos de lenguaje en "
    "tareas reales del proyecto. Cada entrada documenta modelo, "
    "tarea, resultado, tiempo, correcciones humanas, validaciones y "
    "decision de uso futuro.\n"
    "\n"
    "No se registran impresiones generales: solo experimentos "
    "comparables con una tarea definida y un resultado medible. Una "
    "entrada sirve para decidir, en el futuro, que modelo usar para "
    "una tarea parecida.\n"
    "\n"
    "---\n"
    "\n"
)


def append_entry(path: Path, entry: str) -> None:
    """Anade ``entry`` al final de ``path`` de forma atomica.

    - Si ``path.parent`` no existe, lanza ``EvaluationError``.
    - Si ``path`` no existe y su directorio padre si, se crea con el
      encabezado canonico de ``evaluations.md`` seguido de ``entry``.
    - Conserva exactamente el contenido previo.
    - Escritura atomica: archivo temporal en el mismo directorio
      seguido de ``Path.replace()``.
    """
    if not path.parent.is_dir():
        raise EvaluationError(f"directorio padre inexistente: {path.parent}")

    if path.is_file():
        previous = path.read_text(encoding="utf-8")
        if previous and not previous.endswith("\n"):
            previous = previous + "\n"
        if previous and not previous.endswith("\n\n"):
            # Garantizar exactamente una linea en blanco de separacion
            previous = previous + "\n"
        new_content = previous + entry
    else:
        new_content = HEADER_BLOCK + entry

    tmp_path = path.with_name(path.name + ".tmp")
    if tmp_path.exists():
        # Limpiar estado residual de una escritura previa fallida
        tmp_path.unlink()
    try:
        tmp_path.write_text(new_content, encoding="utf-8")
        tmp_path.replace(path)
    finally:
        # Si replace() tuvo exito, el .tmp ya no existe (Path.replace()
        # renombra el origen sobre el destino). Si aun existe, es senal
        # de que write_text o replace fallaron o fueron interrumpidos.
        # Se elimina en finally para cubrir KeyboardInterrupt y cualquier
        # otra excepcion sin capturarla.
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="record_evaluation.py",
        description=(
            "Anade una entrada al registro de evaluaciones "
            "(docs/ai/evaluations.md). Sin --write imprime preview."
        ),
    )
    parser.add_argument("--task", required=True, help="Tarea (obligatorio).")
    parser.add_argument("--agent", required=True, help="Agente (obligatorio).")
    parser.add_argument("--model", required=True, help="Modelo (obligatorio).")
    parser.add_argument("--provider", required=True, help="Proveedor (obligatorio).")
    parser.add_argument(
        "--result",
        required=True,
        choices=sorted(VALID_RESULTS),
        help="Resultado (obligatorio).",
    )
    parser.add_argument(
        "--duration-minutes",
        type=float,
        default=None,
        help="Duracion en minutos (opcional).",
    )
    parser.add_argument(
        "--corrections",
        default="",
        help="Correcciones (opcional).",
    )
    parser.add_argument(
        "--escalated",
        choices=sorted(VALID_ESCALATED),
        default="no",
        help="Escalado (opcional, default 'no').",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Notas (opcional).",
    )
    parser.add_argument(
        "--output",
        default="docs/ai/evaluations.md",
        help="Archivo destino (default: docs/ai/evaluations.md).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Escribe en el archivo. Sin este flag imprime preview.",
    )
    return parser.parse_args(argv)


def _to_evaluation(args: argparse.Namespace) -> Evaluation:
    return Evaluation(
        task=args.task,
        agent=args.agent,
        model=args.model,
        provider=args.provider,
        result=args.result,
        duration_minutes=args.duration_minutes,
        corrections=args.corrections,
        escalated=(args.escalated == "yes"),
        notes=args.notes,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data = _to_evaluation(args)
        validate(data)
    except EvaluationError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    entry = build_entry(data, _dt.date.today())
    output_path = Path(args.output)

    if not args.write:
        print("--- PREVIEW ---")
        print(entry, end="")
        print("--- END PREVIEW ---")
        return 0

    try:
        append_entry(output_path, entry)
    except EvaluationError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"[error] no se pudo escribir {output_path}: {exc}", file=sys.stderr)
        return 1

    print(f"OK: entrada anadida a {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
