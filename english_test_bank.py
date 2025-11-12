"""Utility functions for loading and validating the English test item bank."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence

ALLOWED_SKILLS = {"grammar", "vocab", "reading", "use_of_english"}
REQUIRED_KEYS = {"id", "level", "skill", "type", "prompt", "options", "answer"}
MIN_ITEMS_PER_LEVEL = 20


def load_item_bank(path: str | Path) -> Dict[str, List[Dict]]:
    """Load and validate the question bank from *path*.

    The function enforces the required schema, unique identifiers, that the
    answer exists in the list of options, and that each CEFR level provides a
    reasonable number of items.  Errors raise :class:`ValueError` with
    descriptive messages to simplify debugging.
    """

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Item bank file not found: {file_path}")

    try:
        raw_data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in item bank: {exc}") from exc

    if not isinstance(raw_data, dict):
        raise ValueError("Item bank must be a JSON object mapping levels to item lists.")

    seen_ids: set[str] = set()
    normalized: Dict[str, List[Dict]] = {}

    for level, items in raw_data.items():
        if not isinstance(level, str):
            raise ValueError("Item bank level keys must be strings.")
        if not isinstance(items, list):
            raise ValueError(f"Expected a list of items for level {level}, got {type(items).__name__}.")
        if len(items) < MIN_ITEMS_PER_LEVEL:
            raise ValueError(
                f"Level {level} must contain at least {MIN_ITEMS_PER_LEVEL} items; received {len(items)}."
            )

        validated_items: List[Dict] = []
        for index, entry in enumerate(items, start=1):
            if not isinstance(entry, dict):
                raise ValueError(f"Item {level}[{index}] must be a JSON object.")

            missing = REQUIRED_KEYS - entry.keys()
            if missing:
                identifier = entry.get("id", f"{level}[{index}]")
                raise ValueError(
                    f"Item {identifier} is missing required keys: {', '.join(sorted(missing))}."
                )

            item_id = entry["id"]
            if item_id in seen_ids:
                raise ValueError(f"Duplicate item id detected: {item_id}")
            seen_ids.add(item_id)

            if entry["level"] != level:
                raise ValueError(
                    f"Item {item_id} level mismatch: field={entry['level']} but stored under {level}."
                )

            skill = entry["skill"]
            if skill not in ALLOWED_SKILLS:
                raise ValueError(f"Item {item_id} has unsupported skill '{skill}'.")

            if entry["type"] != "multiple_choice":
                raise ValueError(f"Item {item_id} has unsupported type '{entry['type']}'.")

            prompt = entry["prompt"]
            if not isinstance(prompt, str):
                raise ValueError(f"Item {item_id} prompt must be a string.")

            options = entry["options"]
            _validate_options(item_id, options)

            answer = entry["answer"]
            if not isinstance(answer, str):
                raise ValueError(f"Item {item_id} answer must be a string.")
            if answer not in options:
                raise ValueError(f"Item {item_id} answer '{answer}' is not present in options.")

            explanation = entry.get("explanation")
            if explanation is not None and not isinstance(explanation, str):
                raise ValueError(f"Item {item_id} explanation must be a string if provided.")

            cleaned = {
                "id": item_id,
                "level": level,
                "skill": skill,
                "type": "multiple_choice",
                "prompt": prompt,
                "options": options,
                "answer": answer,
            }
            if explanation is not None:
                cleaned["explanation"] = explanation

            validated_items.append(cleaned)

        normalized[level] = validated_items

    return normalized


def _validate_options(item_id: str, options: Sequence) -> None:
    if not isinstance(options, list):
        raise ValueError(f"Item {item_id} options must be provided as a list.")
    if len(options) < 2:
        raise ValueError(f"Item {item_id} must include at least two options.")
    for option in options:
        if not isinstance(option, str):
            raise ValueError(f"All options for item {item_id} must be strings.")
