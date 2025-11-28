#!/bin/bash
# Скрипт для развёртывания бота на Ubuntu сервере

set -e

echo "🚀 Развёртывание Telegram бота на Ubuntu..."

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Устанавливаю Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker установлен. Перезайдите в систему или выполните: newgrp docker"
    exit 0
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Устанавливаю..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose установлен"
fi

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден. Создаю из примера..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "📝 Отредактируйте файл .env и добавьте ваш BOT_TOKEN:"
        echo "   nano .env"
        exit 1
    else
        echo "❌ Файл env.example не найден!"
        exit 1
    fi
fi

# Проверка наличия BOT_TOKEN
source .env
if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" = "ВАШ_ТОКЕН_ЗДЕСЬ" ]; then
    echo "❌ BOT_TOKEN не установлен в .env файле!"
    echo "   Отредактируйте .env и добавьте ваш токен бота"
    exit 1
fi

# Создание папки для данных
mkdir -p data

# Остановка и удаление старого контейнера (если есть)
echo "🛑 Остановка старого контейнера (если запущен)..."
docker-compose down 2>/dev/null || true

# Сборка и запуск контейнера
echo "🔨 Сборка Docker образа..."
docker-compose build

echo "🚀 Запуск контейнера..."
docker-compose up -d

# Показ логов
echo ""
echo "✅ Бот запущен!"
echo ""
echo "📊 Просмотр логов:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Остановка бота:"
echo "   docker-compose down"
echo ""
echo "🔄 Перезапуск бота:"
echo "   docker-compose restart"
echo ""
echo "📋 Статус:"
docker-compose ps

