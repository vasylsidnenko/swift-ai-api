# utils/gemini_schema_converter.py

import logging
import json
import sys
import os
from pydantic import BaseModel
from typing import Type as PyType, Dict, Any, List, Optional, Union

# Налаштування логування
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Імпортуємо ТІЛЬКИ FunctionDeclaration ---
FunctionDeclaration = None
try:
    from google.generativeai.types import FunctionDeclaration
    logger.info("Успішно імпортовано: FunctionDeclaration з google.generativeai.types")
except ImportError as e:
    logger.error(f"ПОМИЛКА ІМПОРТУ: Не вдалося імпортувати FunctionDeclaration. Помилка: {e}")
    logger.error("Переконайтеся, що бібліотека google-generativeai встановлена та оновлена.")
    logger.error("Спробуйте: pip install --upgrade google-generativeai")
    sys.exit("Критична помилка імпорту.")

if FunctionDeclaration is None:
     logger.critical("Імпорт FunctionDeclaration не вдався!")
     sys.exit("Проблема з доступністю імпортованих імен.")


# --- Мапування типів JSON Schema на РЯДКИ ---
JSON_TO_GEMINI_STRING_MAP = {
    "string": "STRING",
    "integer": "INTEGER",
    "number": "NUMBER",
    "boolean": "BOOLEAN",
    "array": "ARRAY",
    "object": "OBJECT",
}

# --- Функція _convert_pydantic_schema_to_gemini (з версії 3 - повертає СЛОВНИК) ---
def _convert_pydantic_schema_to_gemini(
    pydantic_schema: Dict[str, Any],
    processed_defs: Optional[Dict[str, Dict[str, Any]]] = None
) -> Optional[Dict[str, Any]]:
    """
    Рекурсивна функція для конвертації частини JSON Schema у СЛОВНИК,
    що відповідає структурі, очікуваній FunctionDeclaration.parameters,
    використовуючи РЯДКИ для типів.
    """
    if processed_defs is None: processed_defs = {}
    schema_type_str = pydantic_schema.get("type")

    # --- Обробка $ref ---
    if "$ref" in pydantic_schema:
        ref_path = pydantic_schema["$ref"]
        if ref_path in processed_defs: return processed_defs[ref_path]
        else:
            logger.warning(f"Обробка $ref '{ref_path}' не повністю реалізована.")
            return {'type': "STRING", 'description': f"Reference to {ref_path}"}

    # --- Визначення типу ---
    if not schema_type_str:
        if "properties" in pydantic_schema: schema_type_str = "object"
        elif "items" in pydantic_schema: schema_type_str = "array"
        else:
            any_of = pydantic_schema.get("anyOf")
            if isinstance(any_of, list):
                 non_null_schema = next((s for s in any_of if s.get("type") != "null"), None)
                 if non_null_schema: return _convert_pydantic_schema_to_gemini(non_null_schema, processed_defs)
                 else:
                     logger.warning(f"Не вдалося визначити не-null тип для anyOf: {any_of}. Використовується STRING.")
                     return {'type': "STRING", 'description': pydantic_schema.get("description")}
            logger.warning(f"Не вдалося визначити тип для схеми: {pydantic_schema}. Використовується STRING.")
            schema_type_str = "string"

    gemini_type_str = JSON_TO_GEMINI_STRING_MAP.get(schema_type_str)
    if not gemini_type_str:
        logger.warning(f"Непідтримуваний тип JSON Schema '{schema_type_str}'. Використовується STRING.")
        gemini_type_str = "STRING"

    # --- Створення результату як словника ---
    result_schema: Dict[str, Any] = {'type': gemini_type_str}
    description = pydantic_schema.get("description")
    enum_values = pydantic_schema.get("enum")
    if description: result_schema['description'] = description
    if enum_values and isinstance(enum_values, list): result_schema['enum'] = enum_values

    # --- Обробка складних типів ---
    if gemini_type_str == "OBJECT":
        properties_schema = {}
        required_fields = pydantic_schema.get("required", [])
        pydantic_properties = pydantic_schema.get("properties", {})
        for key, prop_schema in pydantic_properties.items():
            converted_prop = _convert_pydantic_schema_to_gemini(prop_schema, processed_defs)
            if converted_prop: properties_schema[key] = converted_prop
            else:
                logger.error(f"Не вдалося конвертувати властивість '{key}' в об'єкті.")
                properties_schema[key] = {'type': "STRING", 'description': "Помилка конвертації"}
        result_schema['properties'] = properties_schema
        if required_fields: result_schema['required'] = required_fields
    elif gemini_type_str == "ARRAY":
        items_schema = pydantic_schema.get("items")
        if items_schema:
            converted_items = _convert_pydantic_schema_to_gemini(items_schema, processed_defs)
            if converted_items: result_schema['items'] = converted_items
            else:
                 logger.error("Не вдалося конвертувати тип елементів масиву 'items'.")
                 result_schema['items'] = {'type': "STRING", 'description': "Помилка конвертації елементів масиву"}
        else:
            logger.warning("Схема масиву не містить визначення 'items'. Використовується STRING.")
            result_schema['items'] = {'type': "STRING"}
    return result_schema


# --- Функція pydantic_to_gemini_function_declaration (з версії 3 - передає СЛОВНИК) ---
def pydantic_to_gemini_function_declaration(
    name: str,
    description: str,
    pydantic_model: PyType[BaseModel]
) -> FunctionDeclaration:
    """
    Конвертує Pydantic модель у об'єкт FunctionDeclaration, передаючи
    СЛОВНИК як опис параметрів.
    """
    try:
        model_schema = pydantic_model.model_json_schema(ref_template="{model}")
        logger.debug(f"JSON Schema для {pydantic_model.__name__}:\n{json.dumps(model_schema, indent=2)}")
    except Exception as e:
        logger.error(f"Не вдалося згенерувати JSON схему для моделі {pydantic_model.__name__}: {e}")
        raise ValueError(f"Не вдалося отримати JSON схему з {pydantic_model.__name__}") from e

    parameters_dict = _convert_pydantic_schema_to_gemini(model_schema) # Отримуємо словник

    if not isinstance(parameters_dict, dict) or parameters_dict.get('type') != "OBJECT":
        logger.error(f"Конвертована схема параметрів для {name} не є об'єктом або виникла помилка. Результат: {parameters_dict}")
        raise TypeError(f"Не вдалося коректно конвертувати схему параметрів для функції {name}.")

    # Створюємо FunctionDeclaration, передаючи словник
    # Бібліотека google-generativeai повинна сама обробити цей словник
    try:
        return FunctionDeclaration(
            name=name,
            description=description,
            parameters=parameters_dict # Передаємо СЛОВНИК
        )
    except Exception as e:
        logger.error(f"Помилка створення FunctionDeclaration зі словником параметрів: {e}", exc_info=True)
        raise


# --- Приклад використання (ВИПРАВЛЕНО для перевірки СЛОВНИКА в parameters) ---
if __name__ == '__main__':
    # Налаштування шляху
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.join(parent_dir, 'agents'))
    try:
        from ai_models import QuestionModel, QuestionValidation #, CodeTestModel, AnswerLevelModel
        logging.info("Pydantic моделі успішно імпортовано для тестування.")
    except ImportError:
        logging.error("Не вдалося імпортувати моделі з agents.ai_models.", exc_info=True)
        sys.exit(1)

    # --- Тестування QuestionModel ---
    print("\n--- Тестування конвертації QuestionModel ---")
    try:
        question_func_decl = pydantic_to_gemini_function_declaration(
            name="create_programming_question",
            description="Форматує деталі згенерованого питання з програмування.",
            pydantic_model=QuestionModel
        )
        print(f"FunctionDeclaration для QuestionModel створено.")
        print(f"Ім'я: {question_func_decl.name}")

        # --- Перевіряємо СЛОВНИК всередині parameters ---
        params_dict = question_func_decl.parameters # Це має бути словник, який ми передали
        assert isinstance(params_dict, dict)
        assert params_dict.get('type') == "OBJECT"

        # Доступ до властивостей через .get() або ['key']
        props = params_dict.get('properties', {})
        assert "text" in props
        assert props['text'].get('type') == "STRING"
        assert "answerLevels" in props
        assert props['answerLevels'].get('type') == "OBJECT"

        answer_levels_props = props['answerLevels'].get('properties', {})
        assert "beginner" in answer_levels_props
        assert answer_levels_props['beginner'].get('type') == "OBJECT"

        beginner_level_props = answer_levels_props['beginner'].get('properties', {})
        assert "tests" in beginner_level_props
        assert beginner_level_props['tests'].get('type') == "ARRAY"
        # Перевірка items
        items_schema = beginner_level_props['tests'].get('items', {})
        assert items_schema.get('type') == "OBJECT"
        # Перевірка properties всередині items
        items_props = items_schema.get('properties', {})
        assert "snippet" in items_props
        print("Базові перевірки QuestionModel пройшли успішно.")
    except Exception as e:
        logger.error(f"ПОМИЛКА під час конвертації QuestionModel: {e}", exc_info=True)

    # --- Тестування QuestionValidation ---
    print("\n--- Тестування конвертації QuestionValidation ---")
    try:
        validation_func_decl = pydantic_to_gemini_function_declaration(
            name="submit_question_validation",
            description="Форматує детальні результати валідації питання.",
            pydantic_model=QuestionValidation
        )
        print(f"FunctionDeclaration для QuestionValidation створено.")

        # --- Перевіряємо СЛОВНИК всередині parameters ---
        val_params_dict = validation_func_decl.parameters
        assert isinstance(val_params_dict, dict)
        assert val_params_dict.get('type') == "OBJECT"

        val_props = val_params_dict.get('properties', {})
        assert "is_text_clear" in val_props
        assert val_props['is_text_clear'].get('type') == "BOOLEAN"
        assert "quality_score" in val_props
        assert val_props['quality_score'].get('type') == "INTEGER"
        assert "recommendations" in val_props
        assert val_props['recommendations'].get('type') == "ARRAY"
        # Перевірка items
        rec_items = val_props['recommendations'].get('items', {})
        assert rec_items.get('type') == "STRING"

        # Перевірка required
        assert "passed" in val_params_dict.get('required', [])
        print("Базові перевірки QuestionValidation пройшли успішно.")
    except Exception as e:
        logger.error(f"ПОМИЛКА під час конвертації QuestionValidation: {e}", exc_info=True)



