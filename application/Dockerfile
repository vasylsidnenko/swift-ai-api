# 1. Використовуємо офіційний Python образ
FROM python:3.11-slim

# 2. Створюємо робочу директорію
WORKDIR /app

# 3. Копіюємо requirements.txt
COPY requirements.txt .

# 4. Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# 5. Копіюємо весь проект
COPY . .

# 6. Виставляємо змінні середовища для Flask (опціонально)
ENV FLASK_APP=app.py

# 7. Відкриваємо порт
EXPOSE 8080

# 8. Команда запуску
CMD ["python", "app.py"]