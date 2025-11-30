#!/bin/bash
# Скрипт для развёртывания бота с мониторингом (Вариант 2)

set -e

echo "🚀 Развёртывание Telegram бота с мониторингом..."

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
    echo "   Выполните: newgrp docker"
    echo "   Затем запустите скрипт снова: ./deploy-with-monitoring.sh"
    exit 0
fi

# Проверка доступа к Docker
if ! docker ps &> /dev/null; then
    echo "⚠️  Docker установлен, но нет доступа. Активируйте группу docker:"
    echo "   newgrp docker"
    echo "   Затем запустите скрипт снова: ./deploy-with-monitoring.sh"
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

# Загрузка переменных окружения
source .env

# Проверка наличия BOT_TOKEN
if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" = "ВАШ_ТОКЕН_ЗДЕСЬ" ]; then
    echo "❌ BOT_TOKEN не установлен в .env файле!"
    echo "   Отредактируйте .env и добавьте ваш токен бота"
    exit 1
fi

# Установка ENABLE_MONITORING=true если не установлено
if [ -z "$ENABLE_MONITORING" ] || [ "$ENABLE_MONITORING" != "true" ]; then
    echo "📝 Включаю мониторинг в .env файле..."
    if grep -q "ENABLE_MONITORING" .env; then
        sed -i 's/ENABLE_MONITORING=.*/ENABLE_MONITORING=true/' .env
    else
        echo "" >> .env
        echo "# Включить мониторинг" >> .env
        echo "ENABLE_MONITORING=true" >> .env
    fi
    source .env
fi

# Создание папки для данных
mkdir -p data

# Остановка и удаление старых контейнеров (если есть)
echo "🛑 Остановка старых контейнеров (если запущены)..."
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml down 2>/dev/null || true

# Сборка образов
echo "🔨 Сборка Docker образов..."
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml build

# Запуск всех сервисов
echo "🚀 Запуск всех сервисов (бот + Prometheus + Grafana)..."
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Получение IP сервера
SERVER_IP=$(hostname -I | awk '{print $1}')

# Ожидание запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Показ информации
echo ""
echo "✅ Развёртывание завершено!"
echo ""
echo "📊 Сервисы запущены:"
echo "   - Telegram бот: работает"
echo "   - Prometheus: http://${SERVER_IP}:${PROMETHEUS_PORT:-9090}"
echo "   - Grafana: http://${SERVER_IP}:${GRAFANA_PORT:-3000}"
echo "   - Метрики бота: http://${SERVER_IP}:${METRICS_PORT:-8000}/metrics"
echo "   - Health check: http://${SERVER_IP}:${METRICS_PORT:-8000}/health"
echo ""
echo "🔐 Учетные данные Grafana:"
echo "   Логин: ${GRAFANA_USER:-admin}"
echo "   Пароль: ${GRAFANA_PASSWORD:-admin}"
echo ""
echo "📊 Полезные команды:"
echo "   Просмотр логов: docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f"
echo "   Остановка: docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml down"
echo "   Перезапуск: docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml restart"
echo "   Статус: docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml ps"
echo ""
echo "📋 Текущий статус:"
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml ps


