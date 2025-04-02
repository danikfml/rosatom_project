# dashboard/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения
COPY app.py .

# Запускаем Streamlit на порту 8050
CMD ["streamlit", "run", "app.py", "--server.port", "8050", "--server.address", "0.0.0.0"]
