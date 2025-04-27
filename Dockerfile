FROM python:3.11-slim

# Робоча директорія всередині контейнера
WORKDIR /app

# Копіюємо requirements.txt і встановлюємо залежності
COPY mcp_server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь проект
COPY ./mcp_server /app/mcp_server

# Задаємо змінні середовища
ENV PYTHONPATH=/app/mcp_server

# Відкриваємо порт
EXPOSE 10001

# Команда запуску
CMD ["uvicorn", "mcp_main:app", "--host", "0.0.0.0", "--port", "10001"]