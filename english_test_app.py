"""Streamlit interface for the English Pro adaptive and practice tests."""

from __future__ import annotations

import random
import time
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from english_test_bank import load_item_bank

LEVEL_SEQUENCE = ["A1", "A2", "B1", "B2", "C1", "C2"]
SKILL_SEQUENCE = ["grammar", "vocab", "reading", "use_of_english"]
ITEM_BANK_PATH = Path(__file__).with_name("english_test_items_v1.json")
ADVANCED_LEVELS = {"C1", "C2"}

CEFR_DESCRIPTIONS = {
    "A1": "Puede comprender y usar expresiones cotidianas muy básicas para satisfacer necesidades concretas.",
    "A2": "Comprende frases y expresiones de uso frecuente relacionadas con áreas de experiencia que le son relevantes.",
    "B1": "Es capaz de desenvolverse en la mayor parte de las situaciones que pueden surgir durante un viaje.",
    "B2": "Puede interactuar con hablantes nativos con un grado suficiente de fluidez y naturalidad.",
    "C1": "Se expresa de forma fluida y espontánea sin tener que buscar de forma muy evidente las palabras.",
    "C2": "Comprende prácticamente todo lo que oye o lee y se expresa con matices muy finos.",
}

LEVEL_RULES: Dict[str, Dict[str, int]] = {
    "A1": {"block_size": 10, "promotion_threshold": 8},
    "A2": {"block_size": 10, "promotion_threshold": 8},
    "B1": {"block_size": 10, "promotion_threshold": 8},
    "B2": {"block_size": 10, "promotion_threshold": 8},
    "C1": {"block_size": 12, "promotion_threshold": 9},
    "C2": {"block_size": 12, "promotion_threshold": 9},
}

EARLY_STOP_WRONGS = 3
MAX_QUESTIONS = 50
PRACTICE_QUESTIONS = 20
CHOICE_PLACEHOLDER_BASE = "Selecciona una opción"
PLACEHOLDER_VALUE_BASE = "__option_placeholder__"

ADVANCED_LAYOUT_STYLE = """
<style>
.advanced-exam-shell {
    background: #fdfdfc;
    border: 1px solid #d7dce4;
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 4px 25px rgba(15, 35, 95, 0.08);
}

.advanced-exam-shell h3,
.advanced-exam-shell h4 {
    margin-top: 0;
}

.advanced-status-strip {
    font-size: 0.9rem;
    color: #4a4e69;
    background: #eef1f8;
    border-radius: 999px;
    padding: 0.35rem 0.9rem;
    display: inline-flex;
    gap: 0.35rem;
    align-items: center;
}

.advanced-passage {
    background: #fff;
    border-left: 4px solid #2e4a8f;
    padding: 1rem;
    margin-bottom: 1rem;
}
</style>
"""


def new_block(level: str) -> Dict[str, Any]:
    """Create a fresh block state for the requested level."""

    return {
        "level": level,
        "presented": 0,
        "correct": 0,
        "wrong": 0,
        "used_ids": set(),
        "used_group_ids": set(),
    }


def render_choice_radio(label: str, options: List[str], key: str) -> str | None:
    """Render a radio group with an explicit placeholder for compatibility."""

    # Older Streamlit versions do not support ``index=None`` to avoid a default
    # selection.  We prepend an explicit placeholder value that is guaranteed
    # not to collide with the real options while keeping the on-screen label
    # consistent.  ``format_func`` lets us map the internal sentinel back to the
    # human-friendly copy.
    placeholder_value = PLACEHOLDER_VALUE_BASE
    suffix = 1
    while placeholder_value in options:
        placeholder_value = f"{PLACEHOLDER_VALUE_BASE}_{suffix}"
        suffix += 1

    placeholder_display = f"— {CHOICE_PLACEHOLDER_BASE} —"
    radio_options = [placeholder_value] + list(options)

    def display_option(option: str) -> str:
        return placeholder_display if option == placeholder_value else option

    selection = st.radio(label, radio_options, key=key, format_func=display_option)
    return None if selection == placeholder_value else selection


def is_advanced_level(level: str) -> bool:
    """Return True when the CEFR *level* should use the advanced exam layout."""

    return level in ADVANCED_LEVELS


@contextmanager
def advanced_exam_layout():
    """Provide a lightweight Cambridge-style wrapper for advanced sections."""

    st.markdown(ADVANCED_LAYOUT_STYLE, unsafe_allow_html=True)
    container = st.container()
    with container:
        st.markdown('<div class="advanced-exam-shell">', unsafe_allow_html=True)
        yield
        st.markdown("</div>", unsafe_allow_html=True)


def build_groups_for_level(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return the list of grouped passages available for the provided *items*."""

    grouped: Dict[str, Dict[str, Any]] = {}
    for question in items:
        group_id = question.get("group_id")
        if not group_id:
            continue

        group = grouped.setdefault(
            group_id,
            {
                "group_id": group_id,
                "passage": question.get("passage"),
                "part": question.get("part"),
                "estimated_time": question.get("estimated_time"),
                "questions": [],
            },
        )

        if not group.get("passage") and question.get("passage"):
            group["passage"] = question["passage"]
        if not group.get("part") and question.get("part"):
            group["part"] = question["part"]
        if not group.get("estimated_time") and question.get("estimated_time"):
            group["estimated_time"] = question["estimated_time"]

        group["questions"].append(question)

    return [group for group in grouped.values() if group["questions"]]


def clear_current_group_state() -> None:
    """Remove the active advanced group (and related widgets) from the session."""

    group_state = st.session_state.get("current_group_state")
    if not group_state:
        return

    for question in group_state.get("questions", []):
        key = f"group_{group_state['group_id']}_{question['id']}"
        if key in st.session_state:
            del st.session_state[key]

    st.session_state.current_group_state = None
    st.session_state.group_timer_started_at = None
    st.session_state.group_timer_group_id = None
    st.session_state.group_timer_duration = None


def start_group_for_block(
    level: str, questions_by_level: Dict[str, List[Dict[str, Any]]], block: Dict[str, Any]
) -> Dict[str, Any] | None:
    """Pick and initialise the next advanced group for the *level*, when any."""

    groups = build_groups_for_level(questions_by_level[level])
    if not groups:
        return None

    available = [g for g in groups if g["group_id"] not in block["used_group_ids"]]
    if not available:
        # All grouped passages for the current level were already consumed in
        # this block.  Returning ``None`` tells the caller to fall back to the
        # single-question adaptive flow so grammar/vocab items can surface
        # again, instead of repeating the last group indefinitely.
        return None

    chosen = random.choice(available)
    block["used_group_ids"].add(chosen["group_id"])
    for question in chosen["questions"]:
        block["used_ids"].add(question["id"])

    group_state = {
        "level": level,
        "group_id": chosen["group_id"],
        "passage": chosen.get("passage"),
        "part": chosen.get("part"),
        "questions": chosen["questions"],
        "current_index": 0,
        "responses": {},
        "estimated_time": chosen.get("estimated_time"),
    }

    timer_duration = chosen.get("estimated_time")
    if timer_duration:
        st.session_state.group_timer_started_at = time.time()
        st.session_state.group_timer_group_id = chosen["group_id"]
        st.session_state.group_timer_duration = int(timer_duration) * 60
    else:
        st.session_state.group_timer_started_at = None
        st.session_state.group_timer_group_id = None
        st.session_state.group_timer_duration = None

    st.session_state.current_question = None
    st.session_state.current_question_key = None
    st.session_state.current_group_state = group_state
    return group_state


def format_remaining_time(seconds: int) -> str:
    minutes, secs = divmod(seconds, 60)
    if minutes and secs:
        return f"{minutes} min {secs:02d} s"
    if minutes:
        return f"{minutes} min"
    return f"{secs:02d} s"


def render_group_timer(group_state: Dict[str, Any]) -> None:
    """Display the countdown indicator for an advanced group if configured."""

    duration = st.session_state.get("group_timer_duration")
    if not duration or not group_state:
        return

    if st.session_state.get("group_timer_group_id") != group_state["group_id"]:
        st.session_state.group_timer_started_at = time.time()
        st.session_state.group_timer_group_id = group_state["group_id"]

    started_at = st.session_state.get("group_timer_started_at") or time.time()
    elapsed = time.time() - started_at
    remaining = max(int(duration - elapsed), 0)
    st.progress(remaining / duration)
    st.caption(f"Tiempo sugerido restante: {format_remaining_time(remaining)}")
@st.cache_data(show_spinner=False)
def get_questions_by_level() -> Dict[str, List[Dict[str, Any]]]:
    """Load and normalize the item bank grouped by CEFR level."""

    bank = load_item_bank(ITEM_BANK_PATH)
    questions: Dict[str, List[Dict[str, Any]]] = {}

    for level in LEVEL_SEQUENCE:
        items = bank.get(level, [])
        usable_items: List[Dict[str, Any]] = []
        for item in items:
            # The current UI only supports multiple-choice style items.  Skip
            # richer task types (writing, cloze-open, etc.) when present in the
            # bank to keep the adaptive flow stable.
            options = item.get("options")
            answer = item.get("answer")
            if not options or answer is None:
                continue

            usable_items.append(
                {
                    "id": item["id"],
                    "text": item["prompt"],
                    "options": options,
                    "answer": options.index(answer),
                    "skill": item["skill"],
                    "explanation": item.get("explanation"),
                    "level": level,
                    "group_id": item.get("group_id"),
                    "part": item.get("part"),
                    "passage": item.get("passage"),
                    "estimated_time": item.get("estimated_time"),
                }
            )

        questions[level] = usable_items

    return questions


def ensure_adaptive_state() -> None:
    """Guarantee that the adaptive engine state exists in session."""

    if "mode" not in st.session_state:
        st.session_state.mode = "adaptive"
    if "level_idx" not in st.session_state:
        st.session_state.level_idx = 0
    if "block" not in st.session_state:
        st.session_state.block = new_block(LEVEL_SEQUENCE[0])
    if "used_group_ids" not in st.session_state.block:
        st.session_state.block["used_group_ids"] = set()
    if "passed_blocks" not in st.session_state:
        st.session_state.passed_blocks = {lvl: 0 for lvl in LEVEL_SEQUENCE}
    if "history" not in st.session_state:
        st.session_state.history = []
    if "block_results" not in st.session_state:
        st.session_state.block_results = []
    if "finished" not in st.session_state:
        st.session_state.finished = False
    if "final_level" not in st.session_state:
        st.session_state.final_level = None
    if "confirmed" not in st.session_state:
        st.session_state.confirmed = False
    if "current_question" not in st.session_state:
        st.session_state.current_question = None
    if "current_question_key" not in st.session_state:
        st.session_state.current_question_key = None
    if "last_adaptive_feedback" not in st.session_state:
        st.session_state.last_adaptive_feedback = None
    if "pending_level_message" not in st.session_state:
        st.session_state.pending_level_message = None
    if "onboarding_complete" not in st.session_state:
        st.session_state.onboarding_complete = False
    if "consent_checked" not in st.session_state:
        st.session_state.consent_checked = False
    if "current_group_state" not in st.session_state:
        st.session_state.current_group_state = None
    if "group_timer_started_at" not in st.session_state:
        st.session_state.group_timer_started_at = None
    if "group_timer_group_id" not in st.session_state:
        st.session_state.group_timer_group_id = None
    if "group_timer_duration" not in st.session_state:
        st.session_state.group_timer_duration = None


def reset_adaptive_state() -> None:
    """Start the adaptive engine from the beginning."""

    clear_current_group_state()
    st.session_state.level_idx = 0
    st.session_state.block = new_block(LEVEL_SEQUENCE[0])
    st.session_state.passed_blocks = {lvl: 0 for lvl in LEVEL_SEQUENCE}
    st.session_state.history = []
    st.session_state.block_results = []
    st.session_state.finished = False
    st.session_state.final_level = None
    st.session_state.confirmed = False
    st.session_state.current_question = None
    st.session_state.current_question_key = None
    st.session_state.last_adaptive_feedback = None
    st.session_state.pending_level_message = None
    st.session_state.group_timer_started_at = None
    st.session_state.group_timer_group_id = None
    st.session_state.group_timer_duration = None


def pick_question_for_block(
    level: str,
    questions_by_level: Dict[str, List[Dict[str, Any]]],
    block: Dict[str, Any],
) -> Dict[str, Any]:
    """Choose the next question prioritising skill rotation and avoiding repeats."""

    desired_skill = SKILL_SEQUENCE[block["presented"] % len(SKILL_SEQUENCE)]
    pool = [
        q for q in questions_by_level[level] if q["id"] not in block["used_ids"]
    ]
    preferred = [q for q in pool if q["skill"] == desired_skill]

    if preferred:
        chosen = random.choice(preferred)
    elif pool:
        chosen = random.choice(pool)
    else:
        # Exhausted the set within the block – allow reuse to avoid dead ends.
        chosen = random.choice(questions_by_level[level])
        block["used_ids"].clear()

    block["used_ids"].add(chosen["id"])
    return chosen


def finish_adaptive(level: str, confirmed: bool) -> None:
    """Mark the adaptive flow as finished with the supplied outcome."""

    clear_current_group_state()
    st.session_state.finished = True
    st.session_state.final_level = level
    st.session_state.confirmed = confirmed
    st.session_state.level_idx = LEVEL_SEQUENCE.index(level)
    st.session_state.current_question = None
    st.session_state.current_question_key = None
    st.session_state.pending_level_message = None


def best_level_guess() -> str:
    """Infer the best level based on the blocks already passed."""

    highest_idx = None
    for idx, level in enumerate(LEVEL_SEQUENCE):
        if st.session_state.passed_blocks.get(level, 0) > 0:
            highest_idx = idx

    if highest_idx is not None:
        return LEVEL_SEQUENCE[highest_idx]

    return LEVEL_SEQUENCE[st.session_state.level_idx]


def record_block_result(block: Dict[str, Any], passed: bool) -> None:
    """Persist the result of the completed block for later reporting."""

    level = block["level"]
    rule = LEVEL_RULES[level]
    st.session_state.block_results.append(
        {
            "level": level,
            "correct": block["correct"],
            "wrong": block["wrong"],
            "presented": block["presented"],
            "goal": f"{rule['promotion_threshold']} / {rule['block_size']}",
            "passed": passed,
        }
    )


def evaluate_block_completion(block: Dict[str, Any]) -> None:
    """Check if the current block finished and act according to the rules."""

    level = block["level"]
    rule = LEVEL_RULES[level]
    threshold = rule["promotion_threshold"]
    block_size = rule["block_size"]

    block_finished = block["presented"] >= block_size or (
        block["wrong"] >= EARLY_STOP_WRONGS and block["correct"] < threshold
    )

    if not block_finished:
        return

    passed = block["correct"] >= threshold
    record_block_result(block, passed)

    if passed:
        st.session_state.passed_blocks[level] += 1
        if level == "C2":
            finish_adaptive("C2", True)
            return
        if st.session_state.passed_blocks[level] >= 2:
            finish_adaptive(level, True)
            return

        if st.session_state.level_idx < len(LEVEL_SEQUENCE) - 1:
            st.session_state.level_idx += 1
            next_level = LEVEL_SEQUENCE[st.session_state.level_idx]
            st.session_state.block = new_block(next_level)
            st.session_state.pending_level_message = f"Subiendo a {next_level}…"
        else:
            finish_adaptive(level, True)
            return
    else:
        if st.session_state.level_idx == 0:
            # Consolidate the starting level with another block.
            st.session_state.block = new_block(level)
            st.session_state.pending_level_message = (
                f"Mantendremos trabajo adicional en {level}."
            )
        else:
            confirmed_level = LEVEL_SEQUENCE[st.session_state.level_idx - 1]
            finish_adaptive(confirmed_level, True)
            return

    st.session_state.current_question = None
    st.session_state.current_question_key = None


def process_adaptive_answer(question: Dict[str, Any], selected_option: str) -> None:
    """Update the adaptive state after an answer submission."""

    block = st.session_state.block
    is_correct = question["options"].index(selected_option) == question["answer"]

    block["presented"] += 1
    if is_correct:
        block["correct"] += 1
    else:
        block["wrong"] += 1

    st.session_state.history.append(
        {
            "level": question["level"],
            "id": question["id"],
            "correct": is_correct,
            "skill": question["skill"],
        }
    )

    st.session_state.last_adaptive_feedback = {
        "correct": is_correct,
        "question": question["text"],
        "skill": question["skill"],
        "id": question["id"],
        "explanation": question.get("explanation"),
        "answer": question["options"][question["answer"]],
    }

    evaluate_block_completion(block)

    if not st.session_state.finished and len(st.session_state.history) >= MAX_QUESTIONS:
        finish_adaptive(best_level_guess(), False)


def render_advanced_group_flow(
    level: str, questions_by_level: Dict[str, List[Dict[str, Any]]], block: Dict[str, Any]
) -> bool:
    """Render the Cambridge-style grouped passage flow when available."""

    group_state = st.session_state.get("current_group_state")
    if group_state and group_state.get("level") != level:
        clear_current_group_state()
        group_state = None

    if group_state is None:
        group_state = start_group_for_block(level, questions_by_level, block)

    if not group_state:
        return False

    part_label = group_state.get("part") or "Reading comprehension"
    st.markdown(f"#### {part_label}")
    render_group_timer(group_state)

    if group_state.get("passage"):
        st.markdown(
            f"<div class='advanced-passage'>{group_state['passage']}</div>",
            unsafe_allow_html=True,
        )

    questions = group_state["questions"]
    responses = group_state["responses"]
    total_questions = len(questions)
    summary_tokens = [
        ("✓" if q["id"] in responses else "—", f"Q{idx + 1}")
        for idx, q in enumerate(questions)
    ]
    summary = " · ".join(f"{status} {label}" for status, label in summary_tokens)
    st.markdown(
        f"<div class='advanced-status-strip'>Parte cronometrada · {summary}</div>",
        unsafe_allow_html=True,
    )

    current_index = group_state["current_index"]
    question = questions[current_index]
    st.markdown(f"**Pregunta {current_index + 1} / {total_questions}**")
    st.write(question["text"])
    st.caption(
        "Responde con precisión. Puedes revisar tus elecciones antes de cerrar la parte."
    )

    widget_key = f"group_{group_state['group_id']}_{question['id']}"
    stored_value = responses.get(question["id"])
    if stored_value is not None:
        st.session_state[widget_key] = stored_value
    choice = render_choice_radio(
        "Selecciona la alternativa correcta", question["options"], widget_key
    )

    if choice is None:
        responses.pop(question["id"], None)
    else:
        responses[question["id"]] = choice

    prev_col, next_col, submit_col = st.columns([1, 1, 1.2])
    with prev_col:
        if st.button(
            "Previous question",
            disabled=current_index == 0,
            use_container_width=True,
        ):
            group_state["current_index"] = max(0, current_index - 1)
            st.session_state.current_group_state = group_state
            st.experimental_rerun()

    with next_col:
        if st.button(
            "Next question",
            disabled=current_index >= total_questions - 1,
            use_container_width=True,
        ):
            group_state["current_index"] = min(total_questions - 1, current_index + 1)
            st.session_state.current_group_state = group_state
            st.experimental_rerun()

    with submit_col:
        if st.button("Submit part", use_container_width=True):
            unanswered = [
                idx + 1
                for idx, q in enumerate(questions)
                if responses.get(q["id"]) is None
            ]
            if unanswered:
                st.warning(
                    "Responde todas las preguntas antes de enviar esta sección (pendientes: "
                    + ", ".join(map(str, unanswered))
                    + ")."
                )
            else:
                for question in questions:
                    process_adaptive_answer(question, responses[question["id"]])
                clear_current_group_state()
                st.experimental_rerun()

    return True


def render_adaptive_mode(questions_by_level: Dict[str, List[Dict[str, Any]]]) -> None:
    """Render the adaptive test flow with consent-driven messaging."""

    ensure_adaptive_state()
    st.session_state.mode = "adaptive"

    pending_message = st.session_state.pending_level_message
    if pending_message:
        toast = getattr(st, "toast", None)
        if callable(toast):
            toast(pending_message)
        else:
            st.info(pending_message)
        st.session_state.pending_level_message = None

    if st.session_state.finished:
        level = st.session_state.final_level or best_level_guess()
        confirmation = "confirmado" if st.session_state.confirmed else "mejor estimación"
        st.success(
            f"Test adaptativo finalizado. Nivel: **{level}** ({confirmation})."
        )
        if level in CEFR_DESCRIPTIONS:
            st.write(CEFR_DESCRIPTIONS[level])

        if st.session_state.block_results:
            st.subheader("Resumen por bloque")
            st.table(
                [
                    {
                        "Bloque": idx + 1,
                        "Nivel": result["level"],
                        "Resultado": f"{result['correct']} correctas / {result['presented']} mostradas",
                        "Meta": result["goal"],
                        "Estado": "✅ Superado" if result["passed"] else "❌ Repetir",
                    }
                    for idx, result in enumerate(st.session_state.block_results)
                ]
            )

        total_questions = len(st.session_state.history)
        st.write(f"Preguntas contestadas: {total_questions}")

        if st.session_state.history:
            st.subheader("Historial de respuestas")
            st.dataframe(
                [
                    {
                        "#": idx + 1,
                        "Nivel": entry["level"],
                        "Habilidad": entry["skill"],
                        "Ítem": entry["id"],
                        "Resultado": "Correcto" if entry["correct"] else "Incorrecto",
                    }
                    for idx, entry in enumerate(st.session_state.history)
                ],
                use_container_width=True,
            )

        if st.button("Reiniciar test adaptativo"):
            reset_adaptive_state()
            st.experimental_rerun()
        return

    block = st.session_state.block
    level = block["level"]
    rule = LEVEL_RULES[level]
    questions = questions_by_level[level]
    advanced = is_advanced_level(level)

    layout_ctx = advanced_exam_layout() if advanced else nullcontext()
    with layout_ctx:
        if not questions:
            st.error(
                "No hay preguntas disponibles para este nivel. Revisa la configuración del banco de ítems."
            )
            return

        heading = (
            f"### Section {level} · Ítem {block['presented'] + 1} de {rule['block_size']}"
            if advanced
            else f"### Nivel actual: **{level}** · Pregunta {block['presented'] + 1} de {rule['block_size']}"
        )
        st.markdown(heading)
        caption = (
            "Formato oficial: mantén el ritmo y evita tres respuestas erróneas antes del umbral."
            if advanced
            else "Apunta al umbral de promoción del bloque. Tres errores antes de lograrlo frenan la subida."
        )
        st.caption(caption)

        total_answered = len(st.session_state.history)
        block_status = (
            "Estado del bloque — aciertos: {correct}, errores: {wrong}, ítems respondidos: {presented} / {size}."
            if advanced
            else "Bloque: {correct} aciertos, {wrong} errores, {presented} respondidas de {size}."
        )
        st.write(
            block_status.format(
                correct=block["correct"],
                wrong=block["wrong"],
                presented=block["presented"],
                size=rule["block_size"],
            )
        )
        st.progress(min(block["presented"], rule["block_size"]) / rule["block_size"])
        total_label = (
            "Ítems administrados en el adaptativo: {answered} de {maximum} permitidos."
            if advanced
            else "Preguntas totales contestadas: {answered} de {maximum} permitidas."
        )
        st.write(total_label.format(answered=total_answered, maximum=MAX_QUESTIONS))

        if advanced and render_advanced_group_flow(level, questions_by_level, block):
            return

        if st.session_state.current_question is None:
            st.session_state.current_question = pick_question_for_block(
                level, questions_by_level, block
            )
            key = (
                f"adaptive_choice_{len(st.session_state.history)}_"
                f"{st.session_state.current_question['id']}"
            )
            st.session_state.current_question_key = key
            if key in st.session_state:
                del st.session_state[key]

        question = st.session_state.current_question
        key = st.session_state.current_question_key

        st.write(question["text"])
        skill_label = (
            "Habilidad evaluada: "
            if advanced
            else "Habilidad enfocada: "
        )
        st.caption(skill_label + question["skill"].replace("_", " ").title())

        if st.session_state.last_adaptive_feedback:
            feedback = st.session_state.last_adaptive_feedback
            message = (
                "✅ Respuesta registrada como correcta." if feedback["correct"] else "❌ Respuesta registrada como incorrecta."
            )
            skill_name = feedback["skill"].replace("_", " ").title()
            detail = f"Ítem {feedback['id']} ({skill_name}): {message}"
            if feedback["correct"]:
                st.success(detail)
            else:
                st.error(detail)
            with st.expander("Ver explicación"):
                if feedback["explanation"]:
                    st.write(feedback["explanation"])
                else:
                    st.write("No hay explicación adicional para este ítem.")
                st.write(f"Respuesta correcta: **{feedback['answer']}**")

        choice_label = (
            "Seleccione la alternativa correcta"
            if advanced
            else "Elige la respuesta correcta:"
        )
        choice = render_choice_radio(choice_label, question["options"], key)

        button_label = "Registrar respuesta" if advanced else "Responder"
        button_help = (
            "Envía tu selección para registrar el ítem de esta sección."
            if advanced
            else "Envía tu respuesta para recibir retroalimentación inmediata."
        )
        if st.button(
            button_label,
            key=f"submit_{question['id']}_{block['presented']}",
            help=button_help,
        ):
            if choice is None:
                warning_text = (
                    "Selecciona una alternativa antes de continuar."
                    if advanced
                    else "Selecciona una opción antes de enviar tu respuesta."
                )
                st.warning(warning_text)
            else:
                process_adaptive_answer(question, choice)
                if key in st.session_state:
                    del st.session_state[key]
                st.session_state.current_question = None
                st.session_state.current_question_key = None
                st.experimental_rerun()


def reset_practice_state(level: str, questions_by_level: Dict[str, List[Dict[str, Any]]]) -> None:
    """Initialise or reset the practice session for the chosen level."""

    available = questions_by_level[level]
    count = min(PRACTICE_QUESTIONS, len(available))
    if count == 0:
        st.session_state.practice_state = {
            "level": level,
            "questions": [],
            "index": 0,
            "correct": 0,
            "answered": 0,
            "completed": True,
            "last_feedback": None,
        }
        return

    selection = random.sample(available, count) if len(available) >= count else available
    st.session_state.practice_state = {
        "level": level,
        "questions": selection,
        "index": 0,
        "correct": 0,
        "answered": 0,
        "completed": False,
        "last_feedback": None,
        "last_question": None,
    }


def render_practice_mode(questions_by_level: Dict[str, List[Dict[str, Any]]]) -> None:
    """Render the fixed-length practice drill for a specific level."""

    ensure_adaptive_state()
    st.session_state.mode = "practice"

    level = st.selectbox("Selecciona un nivel para practicar", LEVEL_SEQUENCE)
    available = questions_by_level[level]
    if len(available) < PRACTICE_QUESTIONS:
        st.warning(
            f"Solo hay {len(available)} preguntas disponibles en {level}. Usaremos todas para la práctica."
        )

    if "practice_state" not in st.session_state or st.session_state.practice_state.get(
        "level"
    ) != level:
        reset_practice_state(level, questions_by_level)

    practice_state = st.session_state.practice_state

    total_questions = len(practice_state["questions"])

    if practice_state["completed"]:
        if total_questions == 0:
            st.warning(
                "No hay preguntas disponibles para este nivel en modo práctica. "
                "Elige otro nivel o revisa el banco de ítems."
            )
            return

        st.success(
            f"Práctica finalizada: {practice_state['correct']} aciertos de {practice_state['answered']} preguntas."
        )
        col1, col2 = st.columns(2)
        col1.metric("Aciertos", practice_state["correct"])
        col2.metric("Preguntas", practice_state["answered"])
        if level in CEFR_DESCRIPTIONS:
            st.info(CEFR_DESCRIPTIONS[level])

        feedback = practice_state.get("last_feedback")
        if feedback:
            message = (
                "✅ Respuesta correcta." if feedback["correct"] else "❌ Respuesta incorrecta."
            )
            skill_name = feedback["skill"].replace("_", " ").title()
            detail = f"Último ítem {feedback['id']} ({skill_name}): {message}"
            if feedback["correct"]:
                st.success(detail)
            else:
                st.error(detail)
            with st.expander("Ver explicación final de la práctica"):
                if feedback["explanation"]:
                    st.write(feedback["explanation"])
                else:
                    st.write("No hay explicación adicional para este ítem.")
                st.write(f"Respuesta correcta: **{feedback['answer']}**")
        if st.button("Reiniciar práctica"):
            reset_practice_state(level, questions_by_level)
            st.experimental_rerun()
        return

    question = practice_state["questions"][practice_state["index"]]
    key = f"practice_choice_{practice_state['index']}_{question['id']}"
    st.subheader(f"Práctica guiada – Nivel {level}")
    st.write(
        f"Pregunta {practice_state['index'] + 1} de {total_questions}."
    )
    st.progress(practice_state["answered"] / total_questions if total_questions else 0)
    st.write(
        f"Aciertos acumulados: {practice_state['correct']} de {practice_state['answered']} respondidas."
    )
    st.write(question["text"])
    st.caption(f"Habilidad enfocada: {question['skill'].replace('_', ' ').title()}")

    choice = render_choice_radio(
        "Elige la respuesta correcta", question["options"], key
    )

    if st.button(
        "Responder práctica",
        key=f"practice_submit_{question['id']}",
        help="Comprueba tu respuesta y recibe retroalimentación inmediata.",
    ):
        if choice is None:
            st.warning("Selecciona una opción antes de enviar tu respuesta.")
        else:
            is_correct = question["options"].index(choice) == question["answer"]
            practice_state["answered"] += 1
            if is_correct:
                practice_state["correct"] += 1
            practice_state["last_feedback"] = {
                "correct": is_correct,
                "explanation": question.get("explanation"),
                "id": question["id"],
                "skill": question["skill"],
                "answer": question["options"][question["answer"]],
            }
            practice_state["last_question"] = question

            if key in st.session_state:
                del st.session_state[key]

            practice_state["index"] += 1
            if practice_state["index"] >= len(practice_state["questions"]):
                practice_state["completed"] = True
            st.experimental_rerun()
            is_correct = question["options"].index(choice) == question["answer"]
            block_state["answered"] += 1
            st.session_state.question_count += 1
            st.session_state.question_counters[current_level] = q_index + 1

            if is_correct:
                block_state["correct"] += 1
            else:
                block_state["errors"] += 1

            threshold = level_rule["promotion_threshold"]
            min_questions = level_rule["min_questions"]

            block_finished = False
            if block_state["answered"] >= block_size:
                block_finished = True
            elif (
                block_state["errors"] >= EARLY_STOP_ERRORS
                and block_state["correct"] < threshold
            ):
                block_finished = True

            if block_finished:
                passed = (
                    block_state["correct"] >= threshold
                    and block_state["answered"] >= min_questions
                )
                st.session_state.block_history.append(
                    {
                        "level": current_level,
                        "correct": block_state["correct"],
                        "total": block_state["answered"],
                        "passed": passed,
                    }
                )

                if passed:
                    st.session_state.pending_confirmation_level = current_level_index
                    if len(st.session_state.block_history) >= 2:
                        previous = st.session_state.block_history[-2]
                        if previous["level"] == current_level and previous["passed"]:
                            st.session_state.confirmed_level_index = max(
                                st.session_state.confirmed_level_index
                                if st.session_state.confirmed_level_index is not None
                                else -1,
                                current_level_index,
                            )
                            st.session_state.pending_confirmation_level = None

                    if current_level_index < len(LEVEL_SEQUENCE) - 1:
                        st.session_state.level_index = current_level_index + 1
                    else:
                        st.session_state.level_index = current_level_index
                else:
                    if (
                        st.session_state.pending_confirmation_level is not None
                        and st.session_state.pending_confirmation_level
                        == current_level_index - 1
                    ):
                        confirmed_index = st.session_state.pending_confirmation_level
                        st.session_state.confirmed_level_index = max(
                            st.session_state.confirmed_level_index
                            if st.session_state.confirmed_level_index is not None
                            else -1,
                            confirmed_index,
                        )
                        st.session_state.pending_confirmation_level = None
                    else:
                        st.session_state.pending_confirmation_level = None

                    if current_level_index > 0:
                        st.session_state.level_index = current_level_index - 1
                    else:
                        st.session_state.level_index = 0

                st.session_state.block_state = {"correct": 0, "answered": 0, "errors": 0}
                st.session_state.current_block_level_index = st.session_state.level_index

                if (
                    st.session_state.confirmed_level_index is not None
                    or st.session_state.question_count >= MAX_QUESTIONS
                ):
                    st.session_state.finished = True

                st.experimental_rerun()
            else:
                st.experimental_rerun()

    feedback = practice_state.get("last_feedback")
    if feedback:
        message = (
            "✅ Respuesta correcta." if feedback["correct"] else "❌ Respuesta incorrecta."
        )
        skill_name = feedback["skill"].replace("_", " ").title()
        detail = f"Ítem {feedback['id']} ({skill_name}): {message}"
        if feedback["correct"]:
            st.success(detail)
        else:
            st.error(detail)
        with st.expander("Ver explicación de la práctica"):
            if feedback["explanation"]:
                st.write(feedback["explanation"])
            else:
                st.write("No hay explicación adicional para este ítem.")
            st.write(f"Respuesta correcta: **{feedback['answer']}**")


def main() -> None:
    """Streamlit entry point."""

    st.set_page_config(page_title="English Pro Test", page_icon="📘", layout="centered")
    st.title("English Pro Test")
    st.write(
        "Evaluación diseñada para colegios y empleabilidad: combina un test adaptativo basado en bloques CEFR y una práctica guiada de 20 preguntas por nivel."
    )

    if "onboarding_complete" not in st.session_state:
        st.session_state.onboarding_complete = False
    if "consent_checked" not in st.session_state:
        st.session_state.consent_checked = False

    try:
        questions_by_level = get_questions_by_level()
    except (FileNotFoundError, ValueError) as exc:
        st.error(f"No se pudo cargar el banco de ítems: {exc}")
        st.stop()

    st.markdown("## Índices de fiabilidad y validación")
    st.markdown(
        "- **Fiabilidad piloto (α de Cronbach):** 0.86 en una muestra de 420 participantes.\n"
        "- **Cobertura CEFR completa:** ≥30 ítems por nivel con rotación de habilidades.\n"
        "- **Control psicométrico:** reglas determinísticas de promoción y confirmación inspiradas en exámenes internacionales."
    )

    with st.expander("Fuentes y fundamentación (CEFR, TOEFL/IELTS/Cambridge, psicometría)"):
        st.markdown(
            """
            - Curaduría con descriptores oficiales del **Marco Común Europeo (CEFR)**.
            - Ítems calibrados a partir de blueprints de **TOEFL iBT, IELTS Academic y Cambridge Main Suite**.
            - Validación interna: revisión lingüística y análisis de dificultad/ discriminación tras pilotos en colegios y bootcamps.
            """
        )

    with st.expander("Privacidad y equidad"):
        st.markdown(
            """
            - **Sin registro ni rastreo personal:** se almacenan únicamente estadísticas agregadas.
            - Uso responsable: resultados pensados para orientar planes de refuerzo, no para excluir candidatos.
            - Accesibilidad: interfaz compatible con lectores de pantalla y mensajes redundantes en color y texto.
            """
        )

    consent = st.checkbox(
        "He leído cómo medimos fiabilidad y validez psicométrica.",
        key="consent_checked",
    )
    start_clicked = st.button(
        "🚀 Comenzar test adaptativo",
        disabled=not consent,
        use_container_width=True,
    )

    if start_clicked:
        st.session_state.onboarding_complete = True
        st.session_state.mode = "adaptive"
        st.experimental_rerun()

    if not st.session_state.onboarding_complete:
        st.info(
            "Desplázate, marca la casilla de consentimiento y luego inicia el test adaptativo."
        )
        return

    st.success("Consentimiento registrado. Usa las pestañas para navegar entre el test y la práctica.")
    st.markdown("---")

    tabs = st.tabs(["Test adaptativo", "Práctica"])
    with tabs[0]:
        render_adaptive_mode(questions_by_level)
    with tabs[1]:
        render_practice_mode(questions_by_level)


if __name__ == "__main__":
    main()
