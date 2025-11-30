#!/bin/bash
# Скрипт для запуска мониторинга (Prometheus + Grafana) на VPS

set -e

echo "📊 Развёртывание системы мониторинга..."

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    exit 1
fi

# Проверка доступа к Docker
if ! docker ps &> /dev/null; then
    echo "⚠️  Нет доступа к Docker. Активируйте группу docker:"
    echo "   newgrp docker"
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен!"
    exit 1
fi

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "   Создайте его из env.example и настройте переменные"
    exit 1
fi

# Загрузка переменных окружения
source .env

# Проверка, что бот уже запущен
if ! docker ps | grep -q telegram-workout-bot; then
    echo "⚠️  Бот не запущен. Запускаю бота..."
    docker-compose -f docker-compose.yml up -d
    sleep 5
fi

# Запуск мониторинга
echo "🚀 Запуск Prometheus и Grafana..."
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d prometheus grafana

# Получение IP сервера
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "✅ Мониторинг запущен!"
echo ""
echo "📊 Доступ к сервисам:"
echo "   - Prometheus: http://${SERVER_IP}:${PROMETHEUS_PORT:-9090}"
echo "   - Grafana: http://${SERVER_IP}:${GRAFANA_PORT:-3000}"
echo "   - Метрики бота: http://${SERVER_IP}:${METRICS_PORT:-8000}/metrics"
echo ""
echo "🔐 Учетные данные Grafana:"
echo "   Логин: ${GRAFANA_USER:-admin}"
echo "   Пароль: ${GRAFANA_PASSWORD:-admin}"
echo ""
echo "📊 Просмотр логов:"
echo "   docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f"
echo ""
echo "🛑 Остановка мониторинга:"
echo "   docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml stop prometheus grafana"
echo ""
echo "📋 Статус:"
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml ps


