FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY ./app/requirements.txt ./requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходники
COPY ./app ./app

# Переменные окружения (если нужно)
ENV PYTHONUNBUFFERED=1

# Запуск бота
CMD ["python", "-m", "app.main"]