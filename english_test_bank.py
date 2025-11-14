"""Utility functions for loading and validating the English test item bank."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence

ALLOWED_SKILLS = {"grammar", "vocab", "reading", "use_of_english", "writing"}
BASE_REQUIRED_KEYS = {"id", "level", "skill", "type", "prompt"}
OPTION_BASED_TYPES = {"multiple_choice", "cloze_mc"}
TEXT_RESPONSE_TYPES = {"cloze_open", "word_formation", "key_transform"}
WRITING_TYPE = "open_text"
SUPPORTED_TYPES = OPTION_BASED_TYPES | TEXT_RESPONSE_TYPES | {WRITING_TYPE}
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

            missing = BASE_REQUIRED_KEYS - entry.keys()
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

            item_type = entry["type"]
            if item_type not in SUPPORTED_TYPES:
                raise ValueError(f"Item {item_id} has unsupported type '{item_type}'.")

            if skill == "writing" and item_type != WRITING_TYPE:
                raise ValueError(f"Writing item {item_id} must use type '{WRITING_TYPE}'.")
            if item_type == WRITING_TYPE and skill != "writing":
                raise ValueError(f"Open text item {item_id} must declare skill 'writing'.")

            prompt = entry["prompt"]
            if not isinstance(prompt, str):
                raise ValueError(f"Item {item_id} prompt must be a string.")

            options = entry.get("options")
            answer = entry.get("answer")

            if item_type in OPTION_BASED_TYPES:
                if "options" not in entry:
                    raise ValueError(f"Item {item_id} must include an 'options' list.")
                _validate_options(item_id, options)

                if "answer" not in entry:
                    raise ValueError(f"Item {item_id} must include an 'answer'.")
                _validate_string_answer(item_id, answer)
                if answer not in options:
                    raise ValueError(
                        f"Item {item_id} answer '{answer}' is not present in options."
                    )
            elif item_type in TEXT_RESPONSE_TYPES:
                if "answer" not in entry:
                    raise ValueError(f"Item {item_id} must include an 'answer'.")
                _validate_string_answer(item_id, answer)
            elif item_type == WRITING_TYPE:
                _ensure_absent(item_id, entry, {"options", "answer"})
                writing_fields = _validate_writing_fields(entry, item_id)

            explanation = entry.get("explanation")
            if explanation is not None and not isinstance(explanation, str):
                raise ValueError(f"Item {item_id} explanation must be a string if provided.")

            cleaned = {
                "id": item_id,
                "level": level,
                "skill": skill,
                "type": item_type,
                "prompt": prompt,
            }

            if options is not None:
                cleaned["options"] = options
            if answer is not None:
                cleaned["answer"] = answer
            if explanation is not None:
                cleaned["explanation"] = explanation

            for optional_key in ("part", "group_id", "passage"):
                optional_value = entry.get(optional_key)
                if optional_value is not None:
                    if not isinstance(optional_value, str):
                        raise ValueError(
                            f"Item {item_id} field '{optional_key}' must be a string if provided."
                        )
                    cleaned[optional_key] = optional_value

            estimated_time = entry.get("estimatedTime")
            if estimated_time is not None:
                if not isinstance(estimated_time, (int, float)) or estimated_time <= 0:
                    raise ValueError(
                        f"Item {item_id} field 'estimatedTime' must be a positive number when provided."
                    )
                cleaned["estimated_time"] = int(estimated_time)

            if item_type == WRITING_TYPE:
                cleaned.update(writing_fields)

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


def _validate_string_answer(item_id: str, answer: object) -> None:
    if not isinstance(answer, str):
        raise ValueError(f"Item {item_id} answer must be a string.")
    if not answer.strip():
        raise ValueError(f"Item {item_id} answer cannot be empty.")


def _ensure_absent(item_id: str, entry: Dict, disallowed_keys: set[str]) -> None:
    for key in disallowed_keys:
        if key in entry:
            raise ValueError(f"Item {item_id} must not define '{key}'.")


def _validate_writing_fields(entry: Dict, item_id: str) -> Dict:
    task_type = entry.get("task_type")
    if not isinstance(task_type, str) or not task_type.strip():
        raise ValueError(f"Writing item {item_id} must provide a non-empty 'task_type'.")

    min_words = entry.get("min_words")
    max_words = entry.get("max_words")
    if not isinstance(min_words, int) or min_words <= 0:
        raise ValueError(f"Writing item {item_id} must define a positive integer 'min_words'.")
    if not isinstance(max_words, int) or max_words < min_words:
        raise ValueError(
            f"Writing item {item_id} must define a 'max_words' integer >= min_words."
        )

    rubric = entry.get("rubric")
    if not isinstance(rubric, list) or not rubric:
        raise ValueError(f"Writing item {item_id} must include a non-empty rubric list.")
    for idx, criterion in enumerate(rubric, start=1):
        if not isinstance(criterion, str) or not criterion.strip():
            raise ValueError(
                f"Writing item {item_id} rubric entry #{idx} must be a non-empty string."
            )

    return {
        "task_type": task_type,
        "min_words": min_words,
        "max_words": max_words,
        "rubric": rubric,
    }
