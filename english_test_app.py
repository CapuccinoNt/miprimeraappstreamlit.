"""
English Pro Test - Streamlit App (Adaptive)

This Streamlit application implements a simplified adaptive English level test.
It presents a series of multiple-choice questions grouped by CEFR level (A1
through C2). The test begins at an intermediate level and moves up or down
based on the user's answers. After a fixed number of questions, it estimates
an overall level and provides feedback.

In a production system you would replace the hard‑coded question bank with a
persistent database, add listening, writing and speaking sections, and adopt
robust psychometric scoring. This code is meant as a starting point for a
full‑featured exam platform.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from english_test_bank import load_item_bank


LEVEL_SEQUENCE = ["A1", "A2", "B1", "B2", "C1", "C2"]
ITEM_BANK_PATH = Path(__file__).with_name("english_test_items_v1.json")


LEVEL_RULES = {
    "A1": {"block_size": 10, "promotion_threshold": 8, "min_questions": 10},
    "A2": {"block_size": 10, "promotion_threshold": 8, "min_questions": 10},
    "B1": {"block_size": 10, "promotion_threshold": 8, "min_questions": 10},
    "B2": {"block_size": 10, "promotion_threshold": 8, "min_questions": 10},
    "C1": {"block_size": 12, "promotion_threshold": 9, "min_questions": 12},
    "C2": {"block_size": 12, "promotion_threshold": 9, "min_questions": 12},
}

EARLY_STOP_ERRORS = 3
MAX_QUESTIONS = 40


@st.cache_data(show_spinner=False)
def get_questions_by_level() -> Dict[str, List[Dict[str, Any]]]:
    """Load the item bank and map each level to question dictionaries."""

    bank = load_item_bank(ITEM_BANK_PATH)
    questions: Dict[str, List[Dict[str, Any]]] = {}
    for level in LEVEL_SEQUENCE:
        level_items = bank.get(level, [])
        if len(level_items) < LEVEL_RULES[level]["block_size"]:
            raise ValueError(
                f"Item bank for level {level} must contain at least "
                f"{LEVEL_RULES[level]['block_size']} items, found {len(level_items)}."
            )
        questions[level] = [
            {
                "id": item["id"],
                "text": item["prompt"],
                "options": item["options"],
                "answer": item["options"].index(item["answer"]),
                "skill": item["skill"],
                "explanation": item.get("explanation"),
            }
            for item in level_items
        ]

    return questions


def determine_final_level(
    block_history: List[Dict[str, Any]],
    confirmed_level_index: Optional[int],
    current_level_index: int,
) -> Dict[str, Any]:
    """Return the best estimate of the user's level and confirmation status."""

    if confirmed_level_index is not None:
        return {
            "level": LEVEL_SEQUENCE[confirmed_level_index],
            "confirmed": True,
        }

    passed_levels = [
        LEVEL_SEQUENCE.index(entry["level"])
        for entry in block_history
        if entry["passed"]
    ]

    if passed_levels:
        best_index = max(passed_levels)
    else:
        best_index = current_level_index

    return {"level": LEVEL_SEQUENCE[best_index], "confirmed": False}


def reset_test_state() -> None:
    """Restore session state variables for a fresh attempt."""

    st.session_state.level_index = LEVEL_SEQUENCE.index("B1")
    st.session_state.question_counters = {lvl: 0 for lvl in LEVEL_SEQUENCE}
    st.session_state.question_count = 0
    st.session_state.block_state = {"correct": 0, "answered": 0, "errors": 0}
    st.session_state.block_history = []
    st.session_state.pending_confirmation_level = None
    st.session_state.confirmed_level_index = None
    st.session_state.finished = False
    st.session_state.current_block_level_index = st.session_state.level_index


def main() -> None:
    """Streamlit entry point that implements the practical scoring rules."""

    st.set_page_config(page_title="English Pro Test", page_icon="📘", layout="centered")
    st.title("English Pro Test")
    st.write(
        "This adaptive quiz follows the practical rules shared by the pedagogy team: "
        "answer blocks of same-level items (10 for A1–B2, 12 for C1–C2) and reach the "
        "required accuracy to move up. Three mistakes before hitting the threshold stop the block early."
    )

    try:
        questions_by_level = get_questions_by_level()
    except (FileNotFoundError, ValueError) as exc:
        st.error(f"Unable to load the item bank: {exc}")
        st.stop()

    if "level_index" not in st.session_state:
        reset_test_state()
    if "question_counters" not in st.session_state:
        st.session_state.question_counters = {lvl: 0 for lvl in LEVEL_SEQUENCE}
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0
    if "block_state" not in st.session_state:
        st.session_state.block_state = {"correct": 0, "answered": 0, "errors": 0}
    if "block_history" not in st.session_state:
        st.session_state.block_history = []
    if "pending_confirmation_level" not in st.session_state:
        st.session_state.pending_confirmation_level = None
    if "confirmed_level_index" not in st.session_state:
        st.session_state.confirmed_level_index = None
    if "finished" not in st.session_state:
        st.session_state.finished = False
    if "current_block_level_index" not in st.session_state:
        st.session_state.current_block_level_index = st.session_state.level_index

    if st.session_state.question_count >= MAX_QUESTIONS:
        st.session_state.finished = True

    if st.session_state.finished or st.session_state.confirmed_level_index is not None:
        result = determine_final_level(
            st.session_state.block_history,
            st.session_state.confirmed_level_index,
            st.session_state.level_index,
        )
        st.success(
            f"Test finished! Estimated level: **{result['level']}**"
            f" ({'confirmed' if result['confirmed'] else 'best guess'})"
        )
        st.write(
            "Level confirmation requires either two successful blocks at the same level "
            "or one success followed by a shortfall at the next level."
        )

        if st.session_state.block_history:
            st.subheader("Block summary")
            history_rows = []
            for index, entry in enumerate(st.session_state.block_history, start=1):
                rule = LEVEL_RULES[entry["level"]]
                history_rows.append(
                    {
                        "Block": index,
                        "Level": entry["level"],
                        "Result": f"{entry['correct']}/{entry['total']}",
                        "Goal": f"{rule['promotion_threshold']} of {rule['block_size']}",
                        "Outcome": "✅ Pass" if entry["passed"] else "❌ Continue",
                    }
                )
            st.table(history_rows)

        if result["confirmed"]:
            st.write(
                "Congratulations! Your level is confirmed. Keep practicing with materials "
                "that match this proficiency to strengthen your skills."
            )
        else:
            st.write(
                "The maximum number of questions was reached before confirmation. "
                "Use the best-guess level as a starting point and consider taking another test block."
            )

        if st.button("Take the test again"):
            reset_test_state()
            st.experimental_rerun()
        return

    current_level_index = st.session_state.level_index
    current_level = LEVEL_SEQUENCE[current_level_index]

    if st.session_state.current_block_level_index != current_level_index:
        st.session_state.block_state = {"correct": 0, "answered": 0, "errors": 0}
        st.session_state.current_block_level_index = current_level_index

    block_state = st.session_state.block_state
    level_rule = LEVEL_RULES[current_level]
    block_goal = level_rule["promotion_threshold"]
    block_size = level_rule["block_size"]

    st.subheader(
        f"Level {current_level} block – question {block_state['answered'] + 1} of {block_size}"
    )
    st.caption(
        f"Need at least {block_goal} correct answers. The block stops early after "
        f"{EARLY_STOP_ERRORS} mistakes before reaching the goal."
    )
    st.write(
        f"Block progress: {block_state['correct']} correct, {block_state['errors']} errors, "
        f"{block_state['answered']} answered so far."
    )
    st.write(f"Total questions answered: {st.session_state.question_count} of {MAX_QUESTIONS}")

    questions_list = questions_by_level[current_level]
    q_index = st.session_state.question_counters[current_level]
    question = questions_list[q_index % len(questions_list)]

    st.write(question["text"])
    choice = st.radio(
        "Choose the correct answer:",
        question["options"],
        index=None,
        key=f"radio_{st.session_state.question_count}",
    )

    if st.button(
        "Submit answer", key=f"submit_{st.session_state.question_count}"
    ):
        if choice is None:
            st.warning("Please select an answer before proceeding.")
        else:
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


if __name__ == "__main__":
    main()
