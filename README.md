# Swift AI API

Цей API генерує питання та відповіді для тестування знань Swift.

## Використання

### Генерація нового питання:
- **Метод:** `POST`
- **URL:** `/generate_question`
- **Тіло запиту:**
  ```json
  {
    "platform": "Apple",
    "keywords": ["memory", "ARC"]
  }