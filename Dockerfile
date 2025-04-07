# Base image
FROM python:3.9

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy API code
COPY . .

# Run API
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]