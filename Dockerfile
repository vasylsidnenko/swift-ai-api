# Базовий образ Python
FROM python:3.9

# Встановлення залежностей
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код API
COPY . .

# Запускаємо API
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]