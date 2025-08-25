FROM python:3.11-slim

WORKDIR /app

COPY ./app/requirements.txt ./app/requirements.txt

# install requirements
RUN pip install --no-cache-dir -r ./app/requirements.txt

COPY ./app ./app

ENV PYTHONUNBUFFERED=1

# Запуск бота
CMD ["python", "app/bot.py"]

# temooraly not work :3