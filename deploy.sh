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
    echo "✅ Docker установлен."
    echo ""
    echo "⚠️  ВАЖНО: Нужно активировать группу docker."
    echo "   Выполните одну из команд:"
    echo "   1. newgrp docker  (рекомендуется, без перезагрузки)"
    echo "   2. Или перезайдите в систему (exit и снова ssh)"
    echo ""
    echo "   После этого запустите скрипт снова: ./deploy.sh"
    exit 0
fi

# Проверка работоспособности Docker
if ! docker ps &> /dev/null; then
    echo "⚠️  Docker установлен, но не работает корректно."
    echo ""
    echo "Возможные причины:"
    echo "  - Нет доступа к Docker (нужно добавить в группу docker)"
    echo "  - Проблемы с установкой Docker"
    echo ""
    echo "Попробуйте:"
    echo "  1. Активировать группу docker: newgrp docker"
    echo "  2. Если не помогло, переустановите Docker:"
    echo "     sudo ./cleanup-docker.sh  (полное удаление)"
    echo "     ./deploy.sh              (установка заново)"
    echo ""
    read -p "Продолжить развёртывание? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        exit 1
    fi
fi

# Проверка доступа к Docker (может быть установлен, но нет прав)
if ! docker ps &> /dev/null; then
    echo "⚠️  Docker установлен, но нет доступа. Активируйте группу docker:"
    echo "   newgrp docker"
    echo "   Затем запустите скрипт снова: ./deploy.sh"
    exit 1
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

# Проверка, нужно ли запускать мониторинг
ENABLE_MONITORING=${ENABLE_MONITORING:-false}
if [ "$ENABLE_MONITORING" = "true" ] || [ "$ENABLE_MONITORING" = "1" ]; then
    echo "📊 Мониторинг включен (Prometheus + Grafana)"
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.monitoring.yml"
else
    echo "📊 Мониторинг отключен (только бот)"
    COMPOSE_FILES="-f docker-compose.yml"
fi

# Остановка и удаление старого контейнера (если есть)
echo "🛑 Остановка старого контейнера (если запущен)..."
docker-compose $COMPOSE_FILES down 2>/dev/null || true

# Сборка и запуск контейнера
echo "🔨 Сборка Docker образа..."
docker-compose $COMPOSE_FILES build

echo "🚀 Запуск контейнера..."
docker-compose $COMPOSE_FILES up -d

# Показ логов
echo ""
echo "✅ Бот запущен!"
if [ "$ENABLE_MONITORING" = "true" ] || [ "$ENABLE_MONITORING" = "1" ]; then
    echo ""
    echo "📊 Мониторинг доступен:"
    echo "   - Prometheus: http://$(hostname -I | awk '{print $1}'):${PROMETHEUS_PORT:-9090}"
    echo "   - Grafana: http://$(hostname -I | awk '{print $1}'):${GRAFANA_PORT:-3000}"
    echo "   - Метрики бота: http://$(hostname -I | awk '{print $1}'):${METRICS_PORT:-8000}/metrics"
fi
echo ""
echo "📊 Просмотр логов:"
echo "   docker-compose $COMPOSE_FILES logs -f"
echo ""
echo "🛑 Остановка:"
echo "   docker-compose $COMPOSE_FILES down"
echo ""
echo "🔄 Перезапуск:"
echo "   docker-compose $COMPOSE_FILES restart"
echo ""
echo "📋 Статус:"
docker-compose $COMPOSE_FILES ps

