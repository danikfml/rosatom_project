FROM python:3.9-slim

WORKDIR /app

# Устанавливаем git для клонирования репозитория
RUN apt-get update && apt-get install -y git

# Отключаем запрос данных (непопадающий в интерактивный режим)
ENV GIT_TERMINAL_PROMPT=0

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY collector.py .

# Запускаем сбор данных
CMD ["python", "collector.py"]
