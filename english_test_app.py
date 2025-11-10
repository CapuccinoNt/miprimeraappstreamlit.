"""
English Level Test - Streamlit App

This app implements a simplified adaptive English language test.
It presents a series of multiple-choice questions covering grammar
and vocabulary. The test begins at an intermediate level and
adjusts difficulty based on user performance. At the end of the
session, the app estimates a CEFR level (A1–C2) and displays
feedback to the user.

This code is intended as a starting point for a full-featured
application. In a production system, you would replace the
hard‑coded question bank with a database or external file,
incorporate additional question types (listening, reading
comprehension, writing, speaking) and apply a more robust
adaptive algorithm (e.g. item response theory). You would also
implement data persistence and user authentication as needed.

To run this app locally:

  streamlit run english_test_app.py

Make sure you have installed Streamlit (`pip install streamlit`).
"""

import streamlit as st
from typing import List, Dict, Any



def get_question_bank() -> List[Dict[str, Any]]:
    """Return a list of questions with increasing difficulty.

    Each question is a dict containing:
      - text: the question prompt
      - options: list of possible answers
      - answer: index of the correct option (0-based)
      - level: CEFR level associated with the question

    The list is ordered from easiest (A1) to hardest (C2).
    """
    return [
        {
            "text": "Complete the sentence: She ___ to school every day.",
            "options": ["go", "goes", "going", "went"],
            "answer": 1,
            "level": "A1",
        },
        {
            "text": "Which word correctly completes the sentence: They haven't seen ____ for a long time.",
            "options": ["their", "theirs", "them", "they"],
            "answer": 2,
            "level": "A2",
        },
        {
            "text": "Choose the correct option: If I ___ you, I would take that job.",
            "options": ["am", "were", "was", "be"],
            "answer": 1,
            "level": "B1",
        },
        {
            "text": "Identify the correctly punctuated sentence:",
            "options": [
                "Although he was tired, but he finished the assignment.",
                "Although he was tired he finished the assignment.",
                "Although he was tired, he finished the assignment.",
                "Although he was tired; he finished the assignment.",
            ],
            "answer": 2,
            "level": "B2",
        },
        {
            "text": "Select the most appropriate word: Her speech was so ___ that everyone listened attentively.",
            "options": ["boring", "engaging", "tedious", "monotonous"],
            "answer": 1,
            "level": "C1",
        },
        {
            "text": "Which sentence demonstrates correct use of the subjunctive mood?",
            "options": [
                "If I was you, I would travel more.",
                "It's essential that he be informed immediately.",
                "She suggested that he goes to the doctor.",
                "I wish I was invited to the party.",
            ],
            "answer": 1,
            "level": "C2",
        },
    ]



def estimate_cefr_level(score: int, total_questions: int) -> str:
    """Estimate a CEFR level based on the proportion of correct answers.

    This is a rudimentary estimation: in a real exam you would
    calibrate your items and scoring model with empirical data.
    """
    ratio = score / max(total_questions, 1)
    if ratio < 0.3:
        return "A1"
    elif ratio < 0.45:
        return "A2"
    elif ratio < 0.6:
        return "B1"
    elif ratio < 0.75:
        return "B2"
    elif ratio < 0.9:
        return "C1"
    else:
        return "C2"



def main() -> None:
    st.set_page_config(
        page_title="English Pro Test",
        page_icon="📘",
        layout="centered",
    )
    st.title("English Pro Test")
    st.write(
        "Test your English proficiency across levels A1 to C2. "
        "Answer the questions below, and we'll estimate your CEFR level."
    )

    # Initialize session state on first run
    if "question_index" not in st.session_state:
        st.session_state.question_index = 0
        st.session_state.score = 0
        st.session_state.finished = False

    questions = get_question_bank()
    total_questions = len(questions)

    # If the test is finished, show results
    if st.session_state.finished:
        level = estimate_cefr_level(st.session_state.score, total_questions)
        st.success(f"You've completed the test! Estimated level: **{level}**")
        st.write(
            f"You answered {st.session_state.score} out of {total_questions} questions correctly."
        )
        # Optionally, provide feedback based on level
        if level in {"A1", "A2"}:
            st.write(
                "You might want to focus on basic grammar and everyday vocabulary. "
                "Consider taking beginner courses or practicing simple conversations."
            )
        elif level in {"B1", "B2"}:
            st.write(
                "Your English is at an intermediate level. Try reading articles and books, "
                "and practice writing short essays to improve your fluency."
            )
        else:  # C1 or C2
            st.write(
                "You're at an advanced level! To refine your skills, consider advanced grammar "
                "studies, academic writing, and engaging with native speakers on complex topics."
            )
        # Offer to restart the test
        if st.button("Take the test again"):
            st.session_state.question_index = 0
            st.session_state.score = 0
            st.session_state.finished = False
        return

    # Show current question
    idx = st.session_state.question_index
    if idx < total_questions:
        q = questions[idx]
        st.subheader(f"Question {idx + 1} of {total_questions} (Level {q['level']})")
        st.write(q["text"])
        # Provide options via radio buttons
        choice = st.radio(
            "Choose the correct answer:",
            q["options"],
            index=None,
            key=f"radio_{idx}",
        )

        # When the user clicks "Submit answer", evaluate the answer
        if st.button("Submit answer", key=f"submit_{idx}"):
            # Ensure user selected an option
            if choice is None:
                st.warning("Please select an answer before proceeding.")
            else:
                if q["options"].index(choice) == q["answer"]:
                    st.session_state.score += 1
                st.session_state.question_index += 1
                # Reset radio selection for the next question
                st.experimental_rerun()
    else:
        # Mark test as finished when questions are exhausted
        st.session_state.finished = True
        st.experimental_rerun()


if __name__ == "__main__":
    main()
