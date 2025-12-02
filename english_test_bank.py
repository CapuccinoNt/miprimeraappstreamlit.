"""Utility functions for loading and validating the English test item bank."""  # Descripción general del módulo para clarificar su propósito
from __future__ import annotations  # Permite usar anotaciones de tipos futuras sin comillas

import json  # Manejo de datos en formato JSON
from pathlib import Path  # Trabajo con rutas de archivos de forma segura
from typing import Dict, List, Sequence  # Tipos estáticos para mayor claridad

ALLOWED_SKILLS = {"grammar", "vocab", "reading", "use_of_english", "writing"}  # Habilidades permitidas en los ítems
BASE_REQUIRED_KEYS = {"id", "level", "skill", "type", "prompt"}  # Campos mínimos que debe tener cada ítem
OPTION_BASED_TYPES = {"multiple_choice"}  # Tipos de ítems que usan opciones cerradas
TEXT_RESPONSE_TYPES = {"cloze_open", "word_formation", "key_transform"}  # Tipos que requieren respuestas de texto
WRITING_TYPE = "open_text"  # Tipo reservado para ejercicios de escritura
CLOZE_CHOICE_TYPE = "cloze_mc"  # Tipo para huecos con opciones múltiples
SUPPORTED_TYPES = OPTION_BASED_TYPES | TEXT_RESPONSE_TYPES | {WRITING_TYPE, CLOZE_CHOICE_TYPE}  # Conjunto total de tipos aceptados
MIN_ITEMS_PER_LEVEL = 0  # Número mínimo de ítems por nivel (aquí se permite cero)


def load_item_bank(path: str | Path) -> Dict[str, List[Dict]]:  # Carga y valida el banco de ítems desde la ruta indicada
    """Load and validate the question bank from *path*.

    The function enforces the required schema, unique identifiers, that the
    answer exists in the list of options, and that each CEFR level provides a
    reasonable number of items.  Errors raise :class:`ValueError` with
    descriptive messages to simplify debugging.
    """

    file_path = Path(path)  # Normaliza la ruta recibida a un objeto Path
    if not file_path.exists():  # Verifica que el archivo exista
        raise FileNotFoundError(f"Item bank file not found: {file_path}")  # Informa si falta el archivo

    try:  # Intenta leer el contenido del JSON de forma segura
        raw_data = json.loads(file_path.read_text(encoding="utf-8"))  # Carga y parsea el archivo como JSON
    except json.JSONDecodeError as exc:  # Captura errores de formato JSON
        raise ValueError(f"Invalid JSON in item bank: {exc}") from exc  # Re-lanza un error descriptivo

    if not isinstance(raw_data, dict):  # Comprueba que la raíz del JSON sea un diccionario
        raise ValueError("Item bank must be a JSON object mapping levels to item lists.")  # Mensaje claro si no lo es

    seen_ids: set[str] = set()  # Conjunto para rastrear identificadores únicos
    normalized: Dict[str, List[Dict]] = {}  # Diccionario final con datos validados por nivel

    for level, items in raw_data.items():  # Recorre cada nivel y su lista de ítems
        if not isinstance(level, str):  # Asegura que la clave del nivel sea texto
            raise ValueError("Item bank level keys must be strings.")  # Error si la clave no es válida
        if not isinstance(items, list):  # Verifica que los ítems estén en una lista
            raise ValueError(f"Expected a list of items for level {level}, got {type(items).__name__}.")  # Describe el problema
        if len(items) < MIN_ITEMS_PER_LEVEL:  # Comprueba la cantidad mínima de ítems por nivel
            raise ValueError(
                f"Level {level} must contain at least {MIN_ITEMS_PER_LEVEL} items; received {len(items)}."
            )  # Advierte si hay menos ítems de los permitidos

        validated_items: List[Dict] = []  # Almacena los ítems ya verificados para este nivel
        for index, entry in enumerate(items, start=1):  # Itera cada ítem con índice humano (desde 1)
            if not isinstance(entry, dict):  # Confirma que el ítem sea un objeto JSON/dict
                raise ValueError(f"Item {level}[{index}] must be a JSON object.")  # Mensaje si no lo es

            missing = BASE_REQUIRED_KEYS - entry.keys()  # Calcula qué claves obligatorias faltan
            if missing:  # Si falta alguna
                identifier = entry.get("id", f"{level}[{index}]")  # Usa el id del ítem o construye uno temporal
                raise ValueError(
                    f"Item {identifier} is missing required keys: {', '.join(sorted(missing))}."
                )  # Explica cuáles faltan

            item_id = entry["id"]  # Toma el identificador del ítem
            if item_id in seen_ids:  # Verifica unicidad del identificador
                raise ValueError(f"Duplicate item id detected: {item_id}")  # Error si se repite
            seen_ids.add(item_id)  # Registra el id como visto

            if entry["level"] != level:  # Comprueba que el nivel declarado coincida con la sección
                raise ValueError(
                    f"Item {item_id} level mismatch: field={entry['level']} but stored under {level}."
                )  # Informa de la inconsistencia

            skill = entry["skill"]  # Extrae la habilidad asociada
            if skill not in ALLOWED_SKILLS:  # Confirma que la habilidad sea aceptada
                raise ValueError(f"Item {item_id} has unsupported skill '{skill}'.")  # Error si no lo es

            item_type = entry["type"]  # Obtiene el tipo de ejercicio
            if item_type not in SUPPORTED_TYPES:  # Verifica si el tipo está permitido
                raise ValueError(f"Item {item_id} has unsupported type '{item_type}'.")  # Mensaje si no se admite

            if skill == "writing" and item_type != WRITING_TYPE:  # Si es habilidad de escritura, debe usar el tipo correcto
                raise ValueError(f"Writing item {item_id} must use type '{WRITING_TYPE}'.")  # Advierte si no coincide
            if item_type == WRITING_TYPE and skill != "writing":  # Si el tipo es de escritura pero la habilidad no
                task_type = entry.get("task_type")  # Obtiene el subtipo de tarea de escritura
                if task_type != "short_answer":  # Permite solo respuestas cortas en este caso especial
                    raise ValueError(
                        "Open text items must either declare skill 'writing' or use task_type 'short_answer'."
                    )  # Explica la regla

            prompt = entry["prompt"]  # Enunciado de la pregunta
            if not isinstance(prompt, str):  # Debe ser texto
                raise ValueError(f"Item {item_id} prompt must be a string.")  # Mensaje si no lo es

            options = entry.get("options")  # Recupera las opciones si existen
            answer = entry.get("answer")  # Recupera la respuesta esperada si existe

            if item_type in OPTION_BASED_TYPES:  # Si el ítem usa opciones
                if "options" not in entry:  # Asegura que estén presentes
                    raise ValueError(f"Item {item_id} must include an 'options' list.")  # Error si faltan
                _validate_options(item_id, options)  # Valida la estructura de las opciones

                if "answer" not in entry:  # Requiere una respuesta en este caso
                    raise ValueError(f"Item {item_id} must include an 'answer'.")  # Indica la ausencia
                _validate_string_answer(item_id, answer)  # Comprueba que la respuesta sea texto válido
                if answer not in options:  # Confirma que la respuesta esté entre las opciones
                    raise ValueError(
                        f"Item {item_id} answer '{answer}' is not present in options."
                    )  # Mensaje si no aparece
            elif item_type == CLOZE_CHOICE_TYPE:  # Para huecos con opciones
                cloze_items = entry.get("cloze_items")  # Lista de huecos
                _validate_cloze_items(item_id, cloze_items, require_options=True)  # Valida cada hueco exigiendo opciones
            elif item_type == "cloze_open":  # Para huecos con respuestas abiertas
                cloze_items = entry.get("cloze_items")  # Lista de huecos
                _validate_cloze_items(item_id, cloze_items, require_options=False)  # Valida huecos sin necesidad de opciones
            elif item_type == "word_formation":  # Para formación de palabras
                wf_items = entry.get("word_formation_items")  # Lista de ejercicios de formación
                _validate_word_formation_items(item_id, wf_items)  # Valida su estructura
            elif item_type == "key_transform":  # Para transformación de oraciones
                tf_items = entry.get("transform_items")  # Lista de transformaciones
                _validate_transform_items(item_id, tf_items)  # Revisa que cada transformación sea correcta
            elif item_type == WRITING_TYPE:  # Para ejercicios de escritura larga
                _ensure_absent(item_id, entry, {"options", "answer"})  # Verifica que no se incluyan campos indebidos
                writing_fields = _validate_writing_fields(entry, item_id)  # Valida campos específicos de escritura

            explanation = entry.get("explanation")  # Explicación opcional del ítem
            if explanation is not None and not isinstance(explanation, str):  # Debe ser texto si está presente
                raise ValueError(f"Item {item_id} explanation must be a string if provided.")  # Error si no cumple

            cleaned = {
                "id": item_id,  # Guarda el identificador final
                "level": level,  # Registra el nivel CEFR
                "skill": skill,  # Habilidad evaluada
                "type": item_type,  # Tipo de ejercicio
                "prompt": prompt,  # Enunciado principal
            }  # Diccionario limpio y listo para usar

            if options is not None:  # Si existen opciones
                cleaned["options"] = options  # Se añaden al diccionario limpio
            if answer is not None:  # Si existe respuesta
                cleaned["answer"] = answer  # Se registra la respuesta
            if explanation is not None:  # Si hay explicación
                cleaned["explanation"] = explanation  # Se guarda para feedback

            for optional_key in ("part", "group_id", "passage"):  # Claves opcionales que podrían aparecer
                optional_value = entry.get(optional_key)  # Obtiene su valor si existe
                if optional_value is not None:  # Solo se procesan si están presentes
                    if not isinstance(optional_value, str):  # Deben ser texto
                        raise ValueError(
                            f"Item {item_id} field '{optional_key}' must be a string if provided."
                        )  # Error si no es texto
                    cleaned[optional_key] = optional_value  # Se incluyen en el diccionario final

            estimated_time = entry.get("estimatedTime")  # Tiempo estimado de resolución
            if estimated_time is not None:  # Si se proporcionó
                if not isinstance(estimated_time, (int, float)) or estimated_time <= 0:  # Debe ser número positivo
                    raise ValueError(
                        f"Item {item_id} field 'estimatedTime' must be a positive number when provided."
                    )  # Mensaje de error si no lo es
                cleaned["estimated_time"] = int(estimated_time)  # Se guarda como entero

            if item_type == WRITING_TYPE:  # Ajustes específicos para escritura
                cleaned.update(writing_fields)  # Añade los campos validados de escritura
            elif item_type in {CLOZE_CHOICE_TYPE, "cloze_open"}:  # Ajustes para ejercicios de huecos
                cleaned["cloze_items"] = entry.get("cloze_items", [])  # Copia la lista de huecos
                cloze_text = entry.get("cloze_text")  # Texto completo con huecos opcional
                if cloze_text:  # Solo si existe contenido
                    cleaned["cloze_text"] = cloze_text  # Se añade al resultado limpio
            elif item_type == "word_formation":  # Ajustes para formación de palabras
                cleaned["word_formation_items"] = entry.get("word_formation_items", [])  # Se copian los ítems
            elif item_type == "key_transform":  # Ajustes para transformaciones clave
                cleaned["transform_items"] = entry.get("transform_items", [])  # Se incorporan los ejercicios

            validated_items.append(cleaned)  # Agrega el ítem validado a la lista del nivel

        normalized[level] = validated_items  # Guarda todos los ítems validados del nivel en el diccionario final

    return normalized  # Devuelve el banco de ítems ya limpio y validado


def _validate_cloze_items(item_id: str, items: object, require_options: bool) -> None:  # Revisa huecos para cloze
    if not isinstance(items, list) or not items:  # Debe ser una lista no vacía
        raise ValueError(f"Item {item_id} must define a non-empty 'cloze_items' list.")  # Error si no cumple

    seen_numbers: set[int] = set()  # Rastrea los números de hueco para evitar duplicados
    for gap in items:  # Recorre cada hueco
        if not isinstance(gap, dict):  # Cada hueco debe ser un diccionario
            raise ValueError(f"Item {item_id} cloze entries must be objects.")  # Mensaje si no lo es

        number = gap.get("number")  # Número del hueco
        if not isinstance(number, int):  # Debe ser entero
            raise ValueError(f"Item {item_id} cloze entries require an integer 'number'.")  # Error si no lo es
        if number in seen_numbers:  # Evita repetir el mismo número
            raise ValueError(f"Item {item_id} repeats cloze number {number}.")  # Advierte duplicados
        seen_numbers.add(number)  # Registra el número como usado

        answer = gap.get("answer")  # Respuesta del hueco
        _validate_string_answer(f"{item_id} gap {number}", answer)  # Verifica que la respuesta sea válida

        options = gap.get("options")  # Opciones para este hueco
        if require_options:  # Si el tipo exige opciones
            _validate_options(f"{item_id} gap {number}", options)  # Se validan las opciones
            if answer not in options:  # Confirma que la respuesta esté incluida
                raise ValueError(
                    f"Item {item_id} gap {number} answer '{answer}' missing from options."
                )  # Error si falta
        elif options is not None:  # Si no son obligatorias pero aparecen
            _validate_options(f"{item_id} gap {number}", options)  # También se validan para mantener coherencia


def _validate_word_formation_items(item_id: str, items: object) -> None:  # Valida ejercicios de formación de palabras
    if not isinstance(items, list) or not items:  # Deben venir como lista y no vacía
        raise ValueError(f"Item {item_id} must define 'word_formation_items'.")  # Error si no cumplen

    for entry in items:  # Recorre cada ejercicio
        if not isinstance(entry, dict):  # Debe ser un diccionario
            raise ValueError(f"Item {item_id} word formation entries must be objects.")  # Error si no lo es

        number = entry.get("number")  # Número del ejercicio
        if not isinstance(number, int):  # Debe ser entero
            raise ValueError(
                f"Item {item_id} word formation entries require an integer 'number'."
            )  # Mensaje si no cumple

        sentence = entry.get("sentence")  # Oración base donde falta la palabra
        base = entry.get("base")  # Palabra raíz que se debe transformar
        if not isinstance(sentence, str) or not isinstance(base, str):  # Ambos valores deben ser texto
            raise ValueError(
                f"Item {item_id} word formation entries need 'sentence' and 'base' strings."
            )  # Error si no lo son

        answer = entry.get("answer")  # Respuesta esperada
        _validate_string_answer(f"{item_id} word {number}", answer)  # Verifica que la respuesta sea válida


def _validate_transform_items(item_id: str, items: object) -> None:  # Revisa ejercicios de transformación
    if not isinstance(items, list) or not items:  # Deben ser lista no vacía
        raise ValueError(f"Item {item_id} must define 'transform_items'.")  # Error si falta o está vacía

    for entry in items:  # Itera cada transformación
        if not isinstance(entry, dict):  # Cada entrada debe ser diccionario
            raise ValueError(f"Item {item_id} transformations must be objects.")  # Mensaje si no lo es

        number = entry.get("number")  # Número del ejercicio
        if not isinstance(number, int):  # Debe ser entero
            raise ValueError(
                f"Item {item_id} transformations require an integer 'number'."
            )  # Advierte si no

        original = entry.get("original")  # Oración original
        keyword = entry.get("keyword")  # Palabra clave que debe usarse
        if not isinstance(original, str) or not isinstance(keyword, str):  # Ambos deben ser cadenas
            raise ValueError(
                f"Item {item_id} transformations need 'original' and 'keyword' strings."
            )  # Error si falta o no son texto

        answer = entry.get("answer")  # Respuesta esperada
        _validate_string_answer(f"{item_id} transform {number}", answer)  # Comprueba que sea cadena no vacía


def _validate_options(item_id: str, options: Sequence) -> None:  # Valida una lista de opciones de respuesta
    if not isinstance(options, list):  # Debe ser lista
        raise ValueError(f"Item {item_id} options must be provided as a list.")  # Error si no
    if len(options) < 2:  # Al menos dos opciones para ser significativo
        raise ValueError(f"Item {item_id} must include at least two options.")  # Mensaje de error si hay menos
    for option in options:  # Recorre cada opción
        if not isinstance(option, str):  # Cada opción debe ser texto
            raise ValueError(f"All options for item {item_id} must be strings.")  # Error si no lo es


def _validate_string_answer(item_id: str, answer: object) -> None:  # Revisa que la respuesta sea cadena válida
    if not isinstance(answer, str):  # Debe ser tipo string
        raise ValueError(f"Item {item_id} answer must be a string.")  # Error si no lo es
    if not answer.strip():  # No puede estar vacía o con solo espacios
        raise ValueError(f"Item {item_id} answer cannot be empty.")  # Mensaje si está vacía


def _ensure_absent(item_id: str, entry: Dict, disallowed_keys: set[str]) -> None:  # Asegura que ciertas claves no existan
    for key in disallowed_keys:  # Recorre las claves prohibidas
        if key in entry:  # Si alguna está presente
            raise ValueError(f"Item {item_id} must not define '{key}'.")  # Se lanza error indicando el problema


def _validate_writing_fields(entry: Dict, item_id: str) -> Dict:  # Valida campos específicos de ejercicios de escritura
    task_type = entry.get("task_type")  # Tipo de tarea de escritura
    if not isinstance(task_type, str) or not task_type.strip():  # Debe ser texto no vacío
        raise ValueError(f"Writing item {item_id} must provide a non-empty 'task_type'.")  # Error si falta o es inválido

    min_words = entry.get("min_words")  # Mínimo de palabras permitido
    max_words = entry.get("max_words")  # Máximo de palabras permitido
    if not isinstance(min_words, int) or min_words <= 0:  # min_words debe ser entero positivo
        raise ValueError(f"Writing item {item_id} must define a positive integer 'min_words'.")  # Mensaje si no cumple
    if not isinstance(max_words, int) or max_words < min_words:  # max_words debe ser entero y no menor que min_words
        raise ValueError(
            f"Writing item {item_id} must define a 'max_words' integer >= min_words."
        )  # Error si la regla no se cumple

    rubric = entry.get("rubric")  # Lista de criterios de evaluación
    if not isinstance(rubric, list) or not rubric:  # Debe ser lista y contener elementos
        raise ValueError(f"Writing item {item_id} must include a non-empty rubric list.")  # Mensaje si falta
    for idx, criterion in enumerate(rubric, start=1):  # Recorre cada criterio con su posición
        if not isinstance(criterion, str) or not criterion.strip():  # Cada criterio debe ser texto no vacío
            raise ValueError(
                f"Writing item {item_id} rubric entry #{idx} must be a non-empty string."
            )  # Error si no cumple

    return {
        "task_type": task_type,  # Devuelve el tipo de tarea
        "min_words": min_words,  # Devuelve el mínimo de palabras
        "max_words": max_words,  # Devuelve el máximo de palabras
        "rubric": rubric,  # Devuelve la lista de criterios
    }  # Diccionario de campos de escritura válidos
