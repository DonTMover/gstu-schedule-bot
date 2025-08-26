#!/bin/bash

set -e  # Остановить скрипт при любой ошибке

# Название образа
IMAGE_NAME="gstu-bot"

echo "🔧 Сборка Docker-образа: $IMAGE_NAME"
docker build -t $IMAGE_NAME .

echo "🚀 Запуск через Docker Compose"
docker compose up -d

echo "✅ Бот запущен!"
