from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from english_test_bank import (
    ALLOWED_SKILLS,
    CLOZE_CHOICE_TYPE,
    OPTION_BASED_TYPES,
    SUPPORTED_TYPES,
    TEXT_RESPONSE_TYPES,
    WRITING_TYPE,
    load_item_bank,
)

BANK_PATH = REPO_ROOT / "english_test_items_v1.json"


def test_item_bank_schema_and_counts() -> None:
    bank = load_item_bank(BANK_PATH)

    expected_levels = {"A1", "A2", "B1", "B2", "C1", "C2"}
    assert expected_levels.issubset(bank.keys()), "Missing CEFR levels in bank"

    seen_ids: set[str] = set()
    for level, items in bank.items():
        for item in items:
            assert item["level"] == level
            assert item["id"] not in seen_ids, f"Duplicate id found: {item['id']}"
            seen_ids.add(item["id"])

            assert item["skill"] in ALLOWED_SKILLS
            assert item["type"] in SUPPORTED_TYPES
            assert isinstance(item["prompt"], str)

            item_type = item["type"]
            if item_type in OPTION_BASED_TYPES:
                assert "options" in item, f"Missing options in {item['id']}"
                assert "answer" in item, f"Missing answer in {item['id']}"
                assert item["answer"] in item["options"], f"Answer missing in options for {item['id']}"
            elif item_type == CLOZE_CHOICE_TYPE:
                cloze = item.get("cloze_items")
                assert cloze, f"Missing cloze items in {item['id']}"
                for gap in cloze:
                    assert gap.get("options"), f"Missing options in gap of {item['id']}"
                    assert gap.get("answer") in gap["options"], f"Gap answer missing in {item['id']}"
            elif item_type in TEXT_RESPONSE_TYPES:
                if item_type == "cloze_open":
                    cloze = item.get("cloze_items")
                    assert cloze, f"Missing cloze items in {item['id']}"
                    for gap in cloze:
                        assert gap.get("answer"), f"Missing gap answer in {item['id']}"
                elif item_type == "word_formation":
                    entries = item.get("word_formation_items")
                    assert entries, f"Missing word formation items in {item['id']}"
                elif item_type == "key_transform":
                    entries = item.get("transform_items")
                    assert entries, f"Missing transformation items in {item['id']}"
            elif item_type == WRITING_TYPE:
                assert "task_type" in item, f"Missing task_type in {item['id']}"
                assert "min_words" in item and "max_words" in item
                assert "rubric" in item and isinstance(item["rubric"], list)


def test_load_item_bank_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_item_bank(REPO_ROOT / "does_not_exist.json")


def test_load_item_bank_invalid_json(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("not json")

    with pytest.raises(ValueError):
        load_item_bank(invalid)


def test_load_item_bank_duplicate_ids(tmp_path: Path) -> None:
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
            },
            {
                "id": "A1-GR-001",
                "level": "A1",
                "skill": "grammar",
                "type": "multiple_choice",
                "prompt": "Test prompt 2",
                "options": ["yes", "no"],
                "answer": "no",
            },
        ]
    }
    path.write_text(__import__("json").dumps(data))

    with pytest.raises(ValueError) as exc:
        load_item_bank(path)

    assert "Duplicate item id" in str(exc.value)


def test_load_item_bank_extended_schema(tmp_path: Path) -> None:
    path = tmp_path / "extended_bank.json"
    items = []
    for idx in range(18):
        items.append(
            {
                "id": f"A1-GR-{idx:03d}",
                "level": "A1",
                "skill": "grammar",
                "type": "multiple_choice",
                "prompt": f"Prompt {idx}",
                "options": ["yes", "no"],
                "answer": "yes",
            }
        )

    items.append(
        {
            "id": "A1-UE-CLZ-001",
            "level": "A1",
            "skill": "use_of_english",
            "type": "cloze_open",
            "prompt": "Fill in the blank.",
            "cloze_items": [{"number": 1, "answer": "word"}],
            "group_id": "A1-UE-CLZ",
        }
    )

    items.append(
        {
            "id": "A1-WR-001",
            "level": "A1",
            "skill": "writing",
            "type": "open_text",
            "prompt": "Write an email.",
            "task_type": "email",
            "min_words": 40,
            "max_words": 60,
            "rubric": ["content", "organization"],
            "part": "writing_short",
        }
    )

    cloned_items = []
    for original in items:
        clone = original.copy()
        clone["id"] = clone["id"].replace("A1", "A2", 1)
        clone["level"] = "A2"
        cloned_items.append(clone)

    data = {"A1": items, "A2": cloned_items}
    path.write_text(json.dumps(data))

    bank = load_item_bank(path)
    writing_items = [item for item in bank["A1"] if item["skill"] == "writing"]
    assert writing_items
    writing = writing_items[0]
    assert writing["type"] == WRITING_TYPE
    assert writing["task_type"] == "email"
    assert writing["min_words"] == 40
    assert writing["part"] == "writing_short"

    cloze_items = [item for item in bank["A1"] if item["type"] == "cloze_open"]
    assert cloze_items and cloze_items[0]["group_id"] == "A1-UE-CLZ"
