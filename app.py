

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

import streamlit as st
from typing import Dict, List, Any


def get_questions_by_level() -> Dict[str, List[Dict[str, Any]]]:
    """Return a dictionary mapping CEFR levels to lists of questions.

    Each question is a dictionary with keys:
      - text: the question prompt.
      - options: a list of possible answers.
      - answer: the index (0-based) of the correct option.

    Questions are grouped by level to allow adaptive selection.
    """
    return {
        "A1": [
            {
                "text": "Complete the sentence: She ___ to school every day.",
                "options": ["go", "goes", "going", "went"],
                "answer": 1,
            },
            {
                "text": "They ___ playing in the park yesterday.",
                "options": ["were", "was", "are", "is"],
                "answer": 0,
            },
            {
                "text": "I ___ a book now.",
                "options": ["read", "am reading", "reads", "readed"],
                "answer": 1,
            },
        ],
        "A2": [
            {
                "text": "Which word correctly completes the sentence: They haven't seen ____ for a long time.",
                "options": ["their", "theirs", "them", "they"],
                "answer": 2,
            },
            {
                "text": "My brother is taller ___ me.",
                "options": ["then", "than", "that", "so"],
                "answer": 1,
            },
            {
                "text": "I enjoy ___ to music.",
                "options": ["listen", "to listen", "listening", "listened"],
                "answer": 2,
            },
        ],
        "B1": [
            {
                "text": "Choose the correct option: If I ___ you, I would take that job.",
                "options": ["am", "were", "was", "be"],
                "answer": 1,
            },
            {
                "text": "She said she ___ the news already.",
                "options": ["has seen", "had seen", "saw", "see"],
                "answer": 1,
            },
            {
                "text": "You need to study hard to ___ the exam.",
                "options": ["pass", "passing", "passed", "passes"],
                "answer": 0,
            },
        ],
        "B2": [
            {
                "text": "Identify the correctly punctuated sentence:",
                "options": [
                    "Although he was tired, but he finished the assignment.",
                    "Although he was tired he finished the assignment.",
                    "Although he was tired, he finished the assignment.",
                    "Although he was tired; he finished the assignment.",
                ],
                "answer": 2,
            },
            {
                "text": "Choose the correct expression: I regret ___ to university earlier.",
                "options": ["not going", "not to go", "not go", "not went"],
                "answer": 0,
            },
            {
                "text": "The project will be finished by the time you ___ back.",
                "options": ["come", "came", "have come", "will come"],
                "answer": 0,
            },
        ],
        "C1": [
            {
                "text": "Select the most appropriate word: Her speech was so ___ that everyone listened attentively.",
                "options": ["boring", "engaging", "tedious", "monotonous"],
                "answer": 1,
            },
            {
                "text": "Choose the sentence with correct parallel structure:",
                "options": [
                    "He not only enjoys to read but also writing poetry.",
                    "He not only enjoys reading but also to write poetry.",
                    "He enjoys not only reading but also writing poetry.",
                    "He enjoys reading not only but also writing poetry.",
                ],
                "answer": 2,
            },
            {
                "text": "Choose the best word to complete the sentence: The findings were ___ to the theory.",
                "options": ["incompatible", "impassive", "incoherent", "incompetent"],
                "answer": 0,
            },
        ],
        "C2": [
            {
                "text": "Which sentence demonstrates correct use of the subjunctive mood?",
                "options": [
                    "If I was you, I would travel more.",
                    "It's essential that he be informed immediately.",
                    "She suggested that he goes to the doctor.",
                    "I wish I was invited to the party.",
                ],
                "answer": 1,
            },
            {
                "text": "Select the correctly used idiom:",
                "options": [
                    "She decided to take the bull by its horns and confront her boss.",
                    "He let the cat out from the bag by mistake.",
                    "They hit the nail on the head with their solution.",
                    "She burned the midnight light to finish the report.",
                ],
                "answer": 2,
            },
            {
                "text": "Choose the option that best completes the sentence: Hardly had I arrived at the station ___ the train left.",
                "options": ["when", "than", "after", "then"],
                "answer": 0,
            },
        ],
    }


def main() -> None:
    """
    Streamlit app entry point. Implements a simple adaptive
    English level test that adjusts difficulty up or down
    depending on the user's answers. The test begins at an
    intermediate level (B1) and asks a fixed number of questions.
    At the end, the user is given a CEFR level and feedback.
    """
    st.set_page_config(
        page_title="English Pro Test",
        page_icon="📘",
        layout="centered",
    )
    st.title("English Pro Test")
    st.write(
        "Test your English proficiency across levels A1 to C2. "
        "Answer the questions below, and we'll adapt the difficulty based on your responses "
        "and estimate your CEFR level."
    )

    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    questions_by_level = get_questions_by_level()

    if "level_index" not in st.session_state:
        st.session_state.level_index = 2
    if "question_counters" not in st.session_state:
        st.session_state.question_counters = {lvl: 0 for lvl in levels}
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "finished" not in st.session_state:
        st.session_state.finished = False

    MAX_QUESTIONS = 10

    if st.session_state.finished:
        final_level = levels[st.session_state.level_index]
        st.success(
            f"You've completed the test! Estimated level: **{final_level}**"
        )
        st.write(
            f"You answered {st.session_state.score} out of {st.session_state.question_count} questions correctly."
        )
        if final_level in {"A1", "A2"}:
            st.write(
                "You might want to focus on basic grammar and everyday vocabulary. "
                "Consider taking beginner courses or practicing simple conversations."
            )
        elif final_level in {"B1", "B2"}:
            st.write(
                "Your English is at an intermediate level. Try reading articles and books, "
                "and practice writing short essays to improve your fluency."
            )
        else:
            st.write(
                "You're at an advanced level! To refine your skills, consider advanced grammar "
                "studies, academic writing, and engaging with native speakers on complex topics."
            )
        if st.button("Take the test again"):
            st.session_state.level_index = 2
            st.session_state.question_counters = {lvl: 0 for lvl in levels}
            st.session_state.question_count = 0
            st.session_state.score = 0
            st.session_state.finished = False
            st.experimental_rerun()
        return

    if st.session_state.question_count >= MAX_QUESTIONS:
        st.session_state.finished = True
        st.experimental_rerun()
        return

    current_level = levels[st.session_state.level_index]
    q_index = st.session_state.question_counters[current_level]
    questions_list = questions_by_level[current_level]
    question = questions_list[q_index % len(questions_list)]

    st.subheader(
        f"Question {st.session_state.question_count + 1} of {MAX_QUESTIONS} (Level {current_level})"
    )
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
            if question["options"].index(choice) == question["answer"]:
                st.session_state.score += 1
                if st.session_state.level_index < len(levels) - 1:
                    st.session_state.level_index += 1
            else:
                if st.session_state.level_index > 0:
                    st.session_state.level_index -= 1
            st.session_state.question_counters[current_level] = q_index + 1
            st.session_state.question_count += 1
            st.experimental_rerun()


if __name__ == "__main__":
    main()
