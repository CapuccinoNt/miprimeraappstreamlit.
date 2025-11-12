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


def new_block(level: str) -> Dict[str, Any]:
    """Create a fresh block state for the requested level."""

    return {
        "level": level,
        "presented": 0,
        "correct": 0,
        "wrong": 0,
        "used_ids": set(),
    }


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
        else:
            finish_adaptive(level, True)
            return
    else:
        if st.session_state.level_idx == 0:
            # Consolidate the starting level with another block.
            st.session_state.block = new_block(level)
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

    evaluate_block_completion(block)

    if not st.session_state.finished and len(st.session_state.history) >= MAX_QUESTIONS:
        finish_adaptive(best_level_guess(), False)


def render_adaptive_mode(questions_by_level: Dict[str, List[Dict[str, Any]]]) -> None:
    """Render the simplified adaptive test flow."""

    ensure_adaptive_state()
    st.session_state.mode = "adaptive"

    if st.session_state.finished:
        level = st.session_state.final_level or best_level_guess()
        confirmation = "confirmed" if st.session_state.confirmed else "best estimate"
        st.success(
            f"Adaptive test finished. Level: **{level}** ({confirmation})."
        )

        if st.session_state.block_results:
            st.subheader("Block summary")
            st.table(
                [
                    {
                        "Block": idx + 1,
                        "Level": result["level"],
                        "Result": f"{result['correct']} correct / {result['presented']} shown",
                        "Goal": result["goal"],
                        "Outcome": "✅ Pass" if result["passed"] else "❌ Repeat",
                    }
                    for idx, result in enumerate(st.session_state.block_results)
                ]
            )

        total_questions = len(st.session_state.history)
        st.write(f"Questions answered: {total_questions}")

        if st.button("Restart adaptive test"):
            reset_adaptive_state()
            st.experimental_rerun()
        return

    block = st.session_state.block
    level = block["level"]
    rule = LEVEL_RULES[level]
    questions = questions_by_level[level]

    st.subheader(f"Adaptive mode – Level {level}")
    st.caption(
        "Reach the promotion threshold to move up. Three mistakes before the goal end the block early."
    )

    total_answered = len(st.session_state.history)
    st.write(
        f"Block progress: {block['correct']} correct, {block['wrong']} wrong, "
        f"{block['presented']} of {rule['block_size']} questions answered."
    )
    st.write(f"Total questions answered: {total_answered} of {MAX_QUESTIONS} allowed.")

    if not questions:
        st.error(
            "No questions available for this level. Please check the item bank configuration."
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
    choice = st.radio(
        "Choose the correct answer:",
        question["options"],
        index=None,
        key=key,
    )

    if st.button("Submit answer", key=f"submit_{question['id']}_{block['presented']}"):
        if choice is None:
            st.warning("Please select an answer before submitting.")
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

    level = st.selectbox("Choose a level for practice", LEVEL_SEQUENCE)
    available = questions_by_level[level]
    if len(available) < PRACTICE_QUESTIONS:
        st.warning(
            f"Only {len(available)} questions available for {level}. Practice will use all of them."
        )

    if "practice_state" not in st.session_state or st.session_state.practice_state.get(
        "level"
    ) != level:
        reset_practice_state(level, questions_by_level)

    practice_state = st.session_state.practice_state

    if practice_state["completed"]:
        st.success(
            f"Practice finished: {practice_state['correct']} correct out of {practice_state['answered']} questions."
        )
        if practice_state.get("last_feedback"):
            st.info(practice_state["last_feedback"])
        if st.button("Restart practice"):
            reset_practice_state(level, questions_by_level)
            st.experimental_rerun()
        return

    question = practice_state["questions"][practice_state["index"]]
    key = f"practice_choice_{practice_state['index']}_{question['id']}"
    if key not in st.session_state:
        st.session_state[key] = None

    st.subheader(f"Practice mode – Level {level}")
    st.write(
        f"Question {practice_state['index'] + 1} of {len(practice_state['questions'])}."
    )
    st.write(question["text"])

    choice = st.radio("Select an answer", question["options"], index=None, key=key)

    if st.button("Submit practice answer", key=f"practice_submit_{question['id']}"):
        if choice is None:
            st.warning("Please choose an option before submitting.")
        else:
            is_correct = question["options"].index(choice) == question["answer"]
            practice_state["answered"] += 1
            if is_correct:
                practice_state["correct"] += 1
                feedback = "✅ Correct!"
            else:
                feedback = "❌ Incorrect."
                if question.get("explanation"):
                    feedback += f" Explanation: {question['explanation']}"
            practice_state["last_feedback"] = feedback
            practice_state["last_question"] = question

            if key in st.session_state:
                del st.session_state[key]

            practice_state["index"] += 1
            if practice_state["index"] >= len(practice_state["questions"]):
                practice_state["completed"] = True
            st.experimental_rerun()

    if practice_state.get("last_feedback"):
        st.info(practice_state["last_feedback"])


def main() -> None:
    """Streamlit entry point."""

    st.set_page_config(page_title="English Pro Test", page_icon="📘", layout="centered")
    st.title("English Pro Test")
    st.write(
        "This app offers a simplified adaptive placement test that follows the pedagogy "
        "team's promotion, confirmation, and early-stop rules, plus a fixed-length practice mode."
    )

    try:
        questions_by_level = get_questions_by_level()
    except (FileNotFoundError, ValueError) as exc:
        st.error(f"Unable to load the item bank: {exc}")
        st.stop()

    mode = st.sidebar.radio(
        "Mode",
        ("Adaptive test", "Practice"),
        index=0 if st.session_state.get("mode", "adaptive") == "adaptive" else 1,
    )

    if mode == "Adaptive test":
        render_adaptive_mode(questions_by_level)
    else:
        render_practice_mode(questions_by_level)


if __name__ == "__main__":
    main()
