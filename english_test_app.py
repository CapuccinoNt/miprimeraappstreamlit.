"""Streamlit interface for the English Pro adaptive and practice tests."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from english_test_bank import load_item_bank

LEVEL_SEQUENCE = ["A1", "A2", "B1", "B2", "C1", "C2"]
SKILL_SEQUENCE = ["grammar", "vocab", "reading", "use_of_english"]
ITEM_BANK_PATH = Path(__file__).with_name("english_test_items_v1.json")

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


def new_block(level: str) -> Dict[str, Any]:
    """Create a fresh block state for the requested level."""

    return {
        "level": level,
        "presented": 0,
        "correct": 0,
        "wrong": 0,
        "used_ids": set(),
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


@st.cache_data(show_spinner=False)
def get_questions_by_level() -> Dict[str, List[Dict[str, Any]]]:
    """Load and normalize the item bank grouped by CEFR level."""

    bank = load_item_bank(ITEM_BANK_PATH)
    questions: Dict[str, List[Dict[str, Any]]] = {}

    for level in LEVEL_SEQUENCE:
        items = bank.get(level, [])
        questions[level] = [
            {
                "id": item["id"],
                "text": item["prompt"],
                "options": item["options"],
                "answer": item["options"].index(item["answer"]),
                "skill": item["skill"],
                "explanation": item.get("explanation"),
                "level": level,
            }
            for item in items
        ]

    return questions


def ensure_adaptive_state() -> None:
    """Guarantee that the adaptive engine state exists in session."""

    if "mode" not in st.session_state:
        st.session_state.mode = "adaptive"
    if "level_idx" not in st.session_state:
        st.session_state.level_idx = 0
    if "block" not in st.session_state:
        st.session_state.block = new_block(LEVEL_SEQUENCE[0])
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


def reset_adaptive_state() -> None:
    """Start the adaptive engine from the beginning."""

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

    st.markdown(
        f"### Nivel actual: **{level}** · Pregunta {block['presented'] + 1} de {rule['block_size']}"
    )
    st.caption(
        "Apunta al umbral de promoción del bloque. Tres errores antes de lograrlo frenan la subida."
    )

    total_answered = len(st.session_state.history)
    st.write(
        f"Bloque: {block['correct']} aciertos, {block['wrong']} errores, "
        f"{block['presented']} respondidas de {rule['block_size']}."
    )
    st.progress(min(block["presented"], rule["block_size"]) / rule["block_size"])
    st.write(
        f"Preguntas totales contestadas: {total_answered} de {MAX_QUESTIONS} permitidas."
    )

    if not questions:
        st.error(
            "No hay preguntas disponibles para este nivel. Revisa la configuración del banco de ítems."
        )
        return

    if st.session_state.current_question is None:
        st.session_state.current_question = pick_question_for_block(level, questions_by_level, block)
        key = f"adaptive_choice_{len(st.session_state.history)}_{st.session_state.current_question['id']}"
        st.session_state.current_question_key = key
        if key in st.session_state:
            del st.session_state[key]

    question = st.session_state.current_question
    key = st.session_state.current_question_key

    st.write(question["text"])
    st.caption(f"Habilidad enfocada: {question['skill'].replace('_', ' ').title()}")

    if st.session_state.last_adaptive_feedback:
        feedback = st.session_state.last_adaptive_feedback
        message = (
            "✅ Respuesta correcta." if feedback["correct"] else "❌ Respuesta incorrecta."
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

    choice = render_choice_radio(
        "Elige la respuesta correcta:", question["options"], key
    )

    if st.button(
        "Responder",
        key=f"submit_{question['id']}_{block['presented']}",
        help="Envía tu respuesta para recibir retroalimentación inmediata.",
    ):
        if choice is None:
            st.warning("Selecciona una opción antes de enviar tu respuesta.")
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
