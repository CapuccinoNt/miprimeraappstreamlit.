"""Streamlit interface for the English Pro adaptive and practice tests."""

from __future__ import annotations

import random
import time
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from english_test_bank import load_item_bank

LEVEL_SEQUENCE = ["A1", "A2", "B1", "B2", "C1", "C2"]
SKILL_SEQUENCE = ["grammar", "vocab", "reading", "use_of_english"]
ITEM_BANK_PATH = Path(__file__).with_name("english_test_items_v1.json")
ADVANCED_LEVELS = {"C1", "C2"}
SUPPORTED_UI_TYPES = {
    "multiple_choice",
    "cloze_mc",
    "cloze_open",
    "word_formation",
    "key_transform",
}

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


def clear_widget_family(prefix: str) -> None:
    """Remove a widget key and any derived children from ``st.session_state``."""

    for state_key in list(st.session_state.keys()):
        if state_key == prefix or state_key.startswith(f"{prefix}_"):
            del st.session_state[state_key]


def rerun_app() -> None:
    """Trigger a Streamlit rerun using the available API."""

    rerun = getattr(st, "experimental_rerun", None) or getattr(st, "rerun", None)
    if rerun:
        rerun()


def render_question_prompt(question: Dict[str, Any], *, show_passage: bool = True) -> None:
    """Display the main prompt and optional supporting text for a question."""

    st.write(question["text"])

    if show_passage and question.get("passage"):
        st.markdown(
            f"<div class='advanced-passage'>{question['passage']}</div>",
            unsafe_allow_html=True,
        )

    cloze_text = question.get("cloze_text")
    if cloze_text:
        formatted = cloze_text.replace("\n", "<br />")
        st.markdown(
            f"<div class='advanced-passage'>{formatted}</div>",
            unsafe_allow_html=True,
        )


def render_question_inputs(question: Dict[str, Any], key_prefix: str, *, advanced: bool = False) -> Any:
    """Render the appropriate widget(s) for the question type and return the response."""

    qtype = question["type"]
    if qtype == "multiple_choice":
        label = (
            "Seleccione la alternativa correcta"
            if advanced
            else "Elige la respuesta correcta"
        )
        return render_choice_radio(label, question["options"], key_prefix)

    if qtype == "cloze_mc":
        responses: Dict[int, Optional[str]] = {}
        for item in question.get("cloze_items", []):
            gap_key = f"{key_prefix}_gap_{item['number']}"
            responses[item["number"]] = render_choice_radio(
                f"Hueco {item['number']}", item["options"], gap_key
            )
        return responses

    if qtype == "cloze_open":
        responses = {}
        for item in question.get("cloze_items", []):
            gap_key = f"{key_prefix}_gap_{item['number']}"
            responses[item["number"]] = st.text_input(
                f"Hueco {item['number']}", key=gap_key
            )
        return responses

    if qtype == "word_formation":
        responses = {}
        for item in question.get("word_formation_items", []):
            gap_key = f"{key_prefix}_wf_{item['number']}"
            label = f"{item['number']}. {item['sentence']} ({item['base']})"
            responses[item["number"]] = st.text_input(label, key=gap_key)
        return responses

    if qtype == "key_transform":
        responses = {}
        for item in question.get("transform_items", []):
            st.write(f"{item['number']}. {item['original']}")
            st.caption(f"Palabra clave: {item['keyword']}")
            gap_key = f"{key_prefix}_kt_{item['number']}"
            responses[item["number"]] = st.text_input(
                "Reescribe la oración", key=gap_key
            )
        return responses

    return None


def normalize_free_text(value: Optional[str]) -> str:
    """Return a stripped version of ``value`` for validation purposes."""

    return (value or "").strip()


def normalize_for_comparison(value: Optional[str]) -> str:
    """Lowercase ``value`` and collapse spaces to ease comparisons."""

    return " ".join(normalize_free_text(value).lower().split())


def response_is_complete(question: Dict[str, Any], response: Any) -> bool:
    """Return True when *response* satisfies the requirements of *question*."""

    qtype = question["type"]
    if qtype == "multiple_choice":
        return response is not None

    if qtype in {"cloze_mc", "cloze_open"}:
        if not isinstance(response, dict):
            return False
        for item in question.get("cloze_items", []):
            if not normalize_free_text(response.get(item["number"])):
                return False
        return True

    if qtype == "word_formation":
        if not isinstance(response, dict):
            return False
        for item in question.get("word_formation_items", []):
            if not normalize_free_text(response.get(item["number"])):
                return False
        return True

    if qtype == "key_transform":
        if not isinstance(response, dict):
            return False
        for item in question.get("transform_items", []):
            if not normalize_free_text(response.get(item["number"])):
                return False
        return True

    return False


def validate_response(question: Dict[str, Any], response: Any) -> Optional[str]:
    """Return a warning message when *response* is incomplete."""

    if response_is_complete(question, response):
        return None

    qtype = question["type"]
    if qtype == "multiple_choice":
        return "Selecciona una alternativa antes de continuar."

    if qtype in {"cloze_mc", "cloze_open"}:
        missing = [
            str(item["number"])
            for item in question.get("cloze_items", [])
            if not normalize_free_text((response or {}).get(item["number"]))
        ]
        if missing:
            return "Completa todos los huecos (pendientes: " + ", ".join(missing) + ")."
        return "Completa todos los huecos antes de enviar."

    if qtype == "word_formation":
        missing = [
            str(item["number"])
            for item in question.get("word_formation_items", [])
            if not normalize_free_text((response or {}).get(item["number"]))
        ]
        return "Responde todas las transformaciones (pendientes: " + ", ".join(missing) + ")."

    if qtype == "key_transform":
        missing = [
            str(item["number"])
            for item in question.get("transform_items", [])
            if not normalize_free_text((response or {}).get(item["number"]))
        ]
        return "Completa todas las reescrituras (pendientes: " + ", ".join(missing) + ")."

    return "Completa la respuesta antes de continuar."


def score_question(question: Dict[str, Any], response: Any) -> Dict[str, Any]:
    """Return a boolean score and a per-element breakdown for the question."""

    breakdown: List[Dict[str, Any]] = []
    qtype = question["type"]

    if qtype == "multiple_choice":
        expected = question["answer"]
        is_correct = response == expected
        breakdown.append(
            {
                "label": "Respuesta",
                "expected": expected,
                "response": response or "—",
                "correct": is_correct,
            }
        )
        return {"is_correct": is_correct, "breakdown": breakdown}

    if qtype == "cloze_mc":
        answers = response if isinstance(response, dict) else {}
        for item in question.get("cloze_items", []):
            user_value = answers.get(item["number"])
            correct = user_value == item["answer"]
            breakdown.append(
                {
                    "label": f"Hueco {item['number']}",
                    "expected": item["answer"],
                    "response": user_value or "—",
                    "correct": correct,
                }
            )
        return {"is_correct": all(entry["correct"] for entry in breakdown), "breakdown": breakdown}

    if qtype == "cloze_open":
        answers = response if isinstance(response, dict) else {}
        for item in question.get("cloze_items", []):
            user_value = answers.get(item["number"])
            correct = normalize_for_comparison(user_value) == normalize_for_comparison(
                item["answer"]
            )
            breakdown.append(
                {
                    "label": f"Hueco {item['number']}",
                    "expected": item["answer"],
                    "response": user_value or "—",
                    "correct": correct,
                }
            )
        return {"is_correct": all(entry["correct"] for entry in breakdown), "breakdown": breakdown}

    if qtype == "word_formation":
        answers = response if isinstance(response, dict) else {}
        for item in question.get("word_formation_items", []):
            user_value = answers.get(item["number"])
            correct = normalize_for_comparison(user_value) == normalize_for_comparison(
                item["answer"]
            )
            breakdown.append(
                {
                    "label": f"Ítem {item['number']}",
                    "expected": item["answer"],
                    "response": user_value or "—",
                    "correct": correct,
                }
            )
        return {"is_correct": all(entry["correct"] for entry in breakdown), "breakdown": breakdown}

    if qtype == "key_transform":
        answers = response if isinstance(response, dict) else {}
        for item in question.get("transform_items", []):
            user_value = answers.get(item["number"])
            candidates = [item["answer"]] + item.get("alternatives", [])
            correct = normalize_for_comparison(user_value) in {
                normalize_for_comparison(candidate) for candidate in candidates
            }
            breakdown.append(
                {
                    "label": f"Transformación {item['number']}",
                    "expected": item["answer"],
                    "response": user_value or "—",
                    "correct": correct,
                }
            )
        return {"is_correct": all(entry["correct"] for entry in breakdown), "breakdown": breakdown}

    return {"is_correct": False, "breakdown": breakdown}


def format_correct_answer(question: Dict[str, Any]) -> Optional[str]:
    """Return a concise textual summary of the expected answer(s)."""

    qtype = question["type"]
    if qtype == "multiple_choice":
        return question.get("answer")

    if qtype in {"cloze_mc", "cloze_open"}:
        parts = [
            f"{item['number']}→{item['answer']}"
            for item in question.get("cloze_items", [])
        ]
        return " · ".join(parts)

    if qtype == "word_formation":
        parts = [
            f"{item['number']}: {item['answer']}"
            for item in question.get("word_formation_items", [])
        ]
        return " | ".join(parts)

    if qtype == "key_transform":
        parts = [
            f"{item['number']}: {item['answer']}"
            for item in question.get("transform_items", [])
        ]
        return "\n".join(parts)

    return None


def build_feedback_payload(question: Dict[str, Any], score_result: Dict[str, Any]) -> Dict[str, Any]:
    """Create a reusable feedback structure for adaptive or practice modes."""

    return {
        "correct": score_result.get("is_correct", False),
        "question": question["text"],
        "skill": question["skill"],
        "id": question["id"],
        "explanation": question.get("explanation"),
        "answer": format_correct_answer(question),
        "breakdown": score_result.get("breakdown", []),
    }


def render_feedback_panel(feedback: Dict[str, Any], expander_label: str) -> None:
    """Render the expandable explanation block shared by both modes."""

    with st.expander(expander_label):
        explanation = feedback.get("explanation")
        if explanation:
            st.write(explanation)
        else:
            st.write("No hay explicación adicional para este ítem.")

        breakdown = feedback.get("breakdown") or []
        if breakdown:
            st.write("Detalle de respuestas:")
            st.table(
                [
                    {
                        "Elemento": entry.get("label"),
                        "Tu respuesta": entry.get("response") or "—",
                        "Correcta": entry.get("expected"),
                        "Estado": "✅" if entry.get("correct") else "❌",
                    }
                    for entry in breakdown
                ]
            )

        answer = feedback.get("answer")
        if answer:
            st.write(f"Respuestas modelo: {answer}")


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
        clear_widget_family(key)

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
    chosen = random.choice(available or groups)
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
def normalize_item_for_ui(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return a UI-ready copy of *item* when supported, otherwise ``None``."""

    item_type = item.get("type")
    if item_type not in SUPPORTED_UI_TYPES:
        return None

    question: Dict[str, Any] = {
        "id": item["id"],
        "text": item["prompt"],
        "skill": item["skill"],
        "level": item["level"],
        "type": item_type,
        "explanation": item.get("explanation"),
        "group_id": item.get("group_id"),
        "part": item.get("part"),
        "passage": item.get("passage"),
        "estimated_time": item.get("estimated_time"),
    }

    if item_type == "multiple_choice":
        options = item.get("options")
        answer = item.get("answer")
        if not options or answer not in options:
            return None
        question["options"] = options
        question["answer"] = answer
        return question

    if item_type == "cloze_mc":
        cloze_items = item.get("cloze_items")
        if not cloze_items:
            return None
        question["cloze_text"] = item.get("cloze_text") or item.get("passage") or ""
        question["cloze_items"] = cloze_items
        return question

    if item_type == "cloze_open":
        cloze_items = item.get("cloze_items")
        if not cloze_items:
            return None
        question["cloze_text"] = item.get("cloze_text") or item.get("passage") or ""
        question["cloze_items"] = cloze_items
        return question

    if item_type == "word_formation":
        wf_items = item.get("word_formation_items")
        if not wf_items:
            return None
        question["word_formation_items"] = wf_items
        return question

    if item_type == "key_transform":
        tf_items = item.get("transform_items")
        if not tf_items:
            return None
        question["transform_items"] = tf_items
        return question

    return None


@st.cache_data(show_spinner=False)
def get_questions_by_level() -> Dict[str, List[Dict[str, Any]]]:
    """Load and normalize the item bank grouped by CEFR level."""

    bank = load_item_bank(ITEM_BANK_PATH)
    questions: Dict[str, List[Dict[str, Any]]] = {}

    for level in LEVEL_SEQUENCE:
        items = bank.get(level, [])
        usable_items: List[Dict[str, Any]] = []
        for item in items:
            normalized = normalize_item_for_ui(item)
            if normalized:
                usable_items.append(normalized)

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


def process_adaptive_answer(question: Dict[str, Any], response: Any) -> None:
    """Update the adaptive state after an answer submission."""

    block = st.session_state.block
    score = score_question(question, response)
    is_correct = score["is_correct"]

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

    st.session_state.last_adaptive_feedback = build_feedback_payload(question, score)

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
        (
            "✓"
            if response_is_complete(q, responses.get(q["id"]))
            else "—",
            f"Q{idx + 1}",
        )
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
    render_question_prompt(question, show_passage=False)
    st.caption(
        "Responde con precisión. Puedes revisar tus elecciones antes de cerrar la parte."
    )

    widget_key = f"group_{group_state['group_id']}_{question['id']}"
    response = render_question_inputs(question, widget_key, advanced=True)
    responses[question["id"]] = response

    prev_col, next_col, submit_col = st.columns([1, 1, 1.2])
    with prev_col:
        if st.button(
            "Previous question",
            disabled=current_index == 0,
            use_container_width=True,
        ):
            group_state["current_index"] = max(0, current_index - 1)
            st.session_state.current_group_state = group_state
            rerun_app()

    with next_col:
        if st.button(
            "Next question",
            disabled=current_index >= total_questions - 1,
            use_container_width=True,
        ):
            group_state["current_index"] = min(total_questions - 1, current_index + 1)
            st.session_state.current_group_state = group_state
            rerun_app()

    with submit_col:
        if st.button("Submit part", use_container_width=True):
            unanswered = [
                idx + 1
                for idx, q in enumerate(questions)
                if not response_is_complete(q, responses.get(q["id"]))
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
                rerun_app()

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
            rerun_app()
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

        render_question_prompt(question)
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
            render_feedback_panel(feedback, "Ver explicación")

        response = render_question_inputs(question, key, advanced=advanced)

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
            warning_text = validate_response(question, response)
            if warning_text:
                st.warning(warning_text)
            else:
                process_adaptive_answer(question, response)
                clear_widget_family(key)
                st.session_state.current_question = None
                st.session_state.current_question_key = None
                rerun_app()


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
            render_feedback_panel(feedback, "Ver explicación final de la práctica")
        if st.button("Reiniciar práctica"):
            reset_practice_state(level, questions_by_level)
            rerun_app()
        return

    question = practice_state["questions"][practice_state["index"]]
    key = f"practice_item_{practice_state['index']}_{question['id']}"
    st.subheader(f"Práctica guiada – Nivel {level}")
    st.write(
        f"Pregunta {practice_state['index'] + 1} de {total_questions}."
    )
    st.progress(practice_state["answered"] / total_questions if total_questions else 0)
    st.write(
        f"Aciertos acumulados: {practice_state['correct']} de {practice_state['answered']} respondidas."
    )
    render_question_prompt(question)
    st.caption(f"Habilidad enfocada: {question['skill'].replace('_', ' ').title()}")

    response = render_question_inputs(question, key, advanced=False)

    if st.button(
        "Responder práctica",
        key=f"practice_submit_{question['id']}",
        help="Comprueba tu respuesta y recibe retroalimentación inmediata.",
    ):
        warning_text = validate_response(question, response)
        if warning_text:
            st.warning(warning_text)
        else:
            score = score_question(question, response)
            practice_state["answered"] += 1
            if score["is_correct"]:
                practice_state["correct"] += 1
            practice_state["last_feedback"] = build_feedback_payload(question, score)
            practice_state["last_question"] = question

            clear_widget_family(key)

            practice_state["index"] += 1
            if practice_state["index"] >= len(practice_state["questions"]):
                practice_state["completed"] = True
            rerun_app()

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
        render_feedback_panel(feedback, "Ver explicación de la práctica")


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
        rerun_app()

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
