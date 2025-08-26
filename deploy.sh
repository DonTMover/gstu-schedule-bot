#!/bin/bash

set -e  # Остановить скрипт при ошибке

IMAGE_NAME="gstu-bot"

echo "Обновление кода из репозитория..."
git pull

echo "🛑 Остановка запущенных контейнеров..."
docker-compose down

echo "🧹 Очистка dangling-образов..."

echo "📊 До очистки:"
df -h /var/lib/docker

docker image prune -f

echo "📊 После очистки:"
df -h /var/lib/docker



echo "🧹 Очистка старых образов (опционально)..."
# docker rmi $IMAGE_NAME  # Раскомментируй, если хочешь удалять старый образ

echo "🔧 Сборка Docker-образа: $IMAGE_NAME"
docker build -t $IMAGE_NAME .

echo "🚀 Запуск через Docker Compose"
docker-compose up -d

echo "✅ Бот перезапущен!"

