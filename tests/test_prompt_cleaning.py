import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from english_test_app import clean_prompt_text


@pytest.mark.parametrize(
    "raw,expected",
    [
        (
            "Parte 3 – Notas tipo mini texto. Texto 8.\n"
            "I get up at 7:00. I have breakfast at 7:30. I go to school at 8:00.\n"
            "Question: When does the person get up?",
            "I get up at 7:00. I have breakfast at 7:30. I go to school at 8:00.\n"
            "Question: When does the person get up?",
        ),
        (
            "Parte A – Choose the correct word (be / have / do / can).\n"
            "Sentence: I ___ 13 years old.",
            "Choose the correct word (be / have / do / can).\nSentence: I ___ 13 years old.",
        ),
    ],
)
def test_clean_prompt_text_strips_metadata_but_keeps_content(raw: str, expected: str) -> None:
    cleaned = clean_prompt_text(raw)
    assert cleaned == expected
