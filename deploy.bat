@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
REM Stop execution on error
SET ERRORLEVEL=0

SET IMAGE_NAME=gstu-bot

echo 🔄 Updating code from repository...
git pull
IF ERRORLEVEL 1 (
    echo Error during git pull
    exit /b 1
)

echo 🛑 Stopping bot container...
docker-compose stop gstu-bot
IF ERRORLEVEL 1 (
    echo Error stopping container
    exit /b 1
)

echo 🧹 Cleaning dangling images...
docker image prune -f
IF ERRORLEVEL 1 (
    echo Error cleaning images
    exit /b 1
)

echo 🔧 Building Docker image: %IMAGE_NAME%
docker build -t %IMAGE_NAME% .
IF ERRORLEVEL 1 (
    echo Error building Docker image
    exit /b 1
)

echo 🚀 Restarting bot (migration runs inside the container)...
docker-compose up -d gstu-bot
IF ERRORLEVEL 1 (
    echo Error starting container
    exit /b 1
)

echo ✅ Bot updated successfully!

