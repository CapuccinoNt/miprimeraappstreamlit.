from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from english_test_bank import ALLOWED_SKILLS, load_item_bank

BANK_PATH = REPO_ROOT / "english_test_items_v1.json"


def test_item_bank_schema_and_counts() -> None:
    bank = load_item_bank(BANK_PATH)

    seen_ids: set[str] = set()
    for level, items in bank.items():
        assert len(items) >= 30, f"Expected at least 30 items for {level}, found {len(items)}"

        skill_counts = Counter()
        for item in items:
            assert item["level"] == level
            assert item["id"] not in seen_ids, f"Duplicate id found: {item['id']}"
            seen_ids.add(item["id"])

            assert set(item).issuperset({"prompt", "options", "answer", "skill", "type"})
            assert item["answer"] in item["options"], f"Answer missing in options for {item['id']}"
            assert item["skill"] in ALLOWED_SKILLS

            skill_counts[item["skill"]] += 1

        total = len(items)
        for skill, count in skill_counts.items():
            share = count / total
            assert 0.2 <= share <= 0.4, (
                f"Skill '{skill}' at level {level} should represent roughly 25-35% of items, got {share:.2%}"
            )


def test_load_item_bank_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_item_bank(REPO_ROOT / "does_not_exist.json")


def test_load_item_bank_invalid_json(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("not json")

    with pytest.raises(ValueError):
        load_item_bank(invalid)


def test_load_item_bank_insufficient_items(tmp_path: Path) -> None:
    path = tmp_path / "bad_bank.json"
    data = {
        "A1": [
            {
                "id": "A1-GR-001",
                "level": "A1",
                "skill": "grammar",
                "type": "multiple_choice",
                "prompt": "Test prompt",
                "options": ["yes", "no"],
                "answer": "yes",
            }
            for _ in range(5)
        ]
    }
    path.write_text(__import__("json").dumps(data))

    with pytest.raises(ValueError) as exc:
        load_item_bank(path)

    assert "at least" in str(exc.value)
