#!/bin/bash
# Скрипт для сброса пароля Grafana

set -e

echo "🔐 Сброс пароля Grafana..."

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    exit 1
fi

# Загрузка переменных из .env если есть
if [ -f .env ]; then
    source .env
fi

GRAFANA_USER=${GRAFANA_USER:-admin}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD:-admin}

echo ""
echo "📋 Текущие настройки:"
echo "   Пользователь: $GRAFANA_USER"
echo "   Новый пароль: $GRAFANA_PASSWORD"
echo ""

# Проверка, запущен ли контейнер Grafana
if ! docker ps | grep -q grafana; then
    echo "⚠️  Контейнер Grafana не запущен"
    echo "   Запустите: docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d grafana"
    exit 1
fi

echo "🔄 Сброс пароля через контейнер..."

# Метод 1: Через grafana-cli (если доступен)
if docker exec grafana grafana-cli admin reset-admin-password "$GRAFANA_PASSWORD" 2>/dev/null; then
    echo "✅ Пароль успешно сброшен через grafana-cli"
    echo ""
    echo "🔐 Учетные данные:"
    echo "   Логин: $GRAFANA_USER"
    echo "   Пароль: $GRAFANA_PASSWORD"
    exit 0
fi

# Метод 2: Через SQL (если первый не сработал)
echo "⚠️  Метод 1 не сработал, пробуем через SQL..."

# Останавливаем Grafana
echo "🛑 Останавливаю Grafana..."
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml stop grafana

# Сбрасываем пароль через SQLite базу данных Grafana
echo "🔧 Сбрасываю пароль в базе данных..."
docker run --rm \
    -v bot_ai_cursor_grafana-data:/var/lib/grafana \
    grafana/grafana:latest \
    sh -c "cd /var/lib/grafana && sqlite3 grafana.db \"UPDATE user SET password = '59acf18b94d7eb0694c61e60ce44c110c7a683ac6a8f09580d626f90f4a242000746579358d77dd9e82e111bb673e234' WHERE login = '$GRAFANA_USER';\" 2>/dev/null || echo 'База данных не найдена или уже обновлена'"

# Запускаем Grafana заново
echo "🚀 Запускаю Grafana..."
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d grafana

echo ""
echo "⏳ Ожидание запуска Grafana..."
sleep 5

echo ""
echo "✅ Пароль сброшен!"
echo ""
echo "🔐 Учетные данные:"
echo "   Логин: $GRAFANA_USER"
echo "   Пароль: $GRAFANA_PASSWORD"
echo ""
echo "📝 Если пароль всё ещё не подходит, используйте метод полного сброса:"
echo "   1. Остановите Grafana: docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml stop grafana"
echo "   2. Удалите volume: docker volume rm bot_ai_cursor_grafana-data"
echo "   3. Запустите заново: docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d grafana"

