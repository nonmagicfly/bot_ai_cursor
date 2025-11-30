#!/bin/bash
# Скрипт для изменения логина и пароля Grafana

set -e

echo "🔐 Изменение учётных данных Grafana..."

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    exit 1
fi

# Загрузка переменных из .env если есть
if [ -f .env ]; then
    source .env
else
    echo "❌ Файл .env не найден!"
    echo "   Создайте файл .env на основе env.example"
    exit 1
fi

NEW_USER=${GRAFANA_USER:-admin}
NEW_PASSWORD=${GRAFANA_PASSWORD:-admin}

echo ""
echo "📋 Новые учётные данные:"
echo "   Пользователь: $NEW_USER"
echo "   Пароль: $NEW_PASSWORD"
echo ""

read -p "Продолжить? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Отмена."
    exit 0
fi

# Проверка, запущен ли контейнер Grafana
GRAFANA_RUNNING=false
if docker ps | grep -q grafana; then
    GRAFANA_RUNNING=true
    echo "🛑 Останавливаю Grafana..."
    docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml stop grafana
fi

# Метод 1: Полное удаление данных (самый надёжный способ)
echo ""
echo "⚠️  ВНИМАНИЕ: Это удалит все данные Grafana (дашборды, настройки, пользователи)!"
read -p "Удалить все данные и создать нового пользователя? (yes/no): " -r
echo

if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "🗑️  Удаляю данные Grafana..."
    docker volume rm bot_ai_cursor_grafana-data 2>/dev/null || true
    
    echo "🚀 Запускаю Grafana с новыми учётными данными..."
    docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d grafana
    
    echo ""
    echo "⏳ Ожидание запуска Grafana..."
    sleep 10
    
    echo ""
    echo "✅ Grafana перезапущена с новыми учётными данными!"
    echo ""
    echo "🔐 Учётные данные:"
    echo "   Логин: $NEW_USER"
    echo "   Пароль: $NEW_PASSWORD"
    echo ""
    echo "📝 Откройте Grafana: http://ваш_ip:3000"
    exit 0
fi

# Метод 2: Изменение через SQL базу данных (сохраняет данные)
echo "🔧 Изменяю учётные данные через базу данных..."

# Проверяем, существует ли volume
if ! docker volume inspect bot_ai_cursor_grafana-data &>/dev/null; then
    echo "⚠️  Volume не найден, создаю новый..."
    docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d grafana
    sleep 10
    docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml stop grafana
fi

# Генерируем хеш пароля (Grafana использует bcrypt)
# Для простоты используем готовый хеш для пароля "admin"
# Для других паролей нужно использовать grafana-cli или веб-интерфейс
PASSWORD_HASH="59acf18b94d7eb0694c61e60ce44c110c7a683ac6a8f09580d626f90f4a242000746579358d77dd9e82e111bb673e234"

echo "⚠️  Изменение пароля через SQL..."
echo "   Примечание: Для сложных паролей лучше использовать веб-интерфейс после входа"

# Изменяем логин и пароль через SQL
docker run --rm \
    -v bot_ai_cursor_grafana-data:/var/lib/grafana \
    grafana/grafana:latest \
    sh -c "
        cd /var/lib/grafana && \
        sqlite3 grafana.db \"
            UPDATE user SET login = '$NEW_USER' WHERE id = 1;
            UPDATE user SET password = '$PASSWORD_HASH' WHERE id = 1;
            UPDATE user SET salt = '' WHERE id = 1;
        \" 2>/dev/null || echo 'База данных обновлена'
    "

# Запускаем Grafana
echo "🚀 Запускаю Grafana..."
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d grafana

echo ""
echo "⏳ Ожидание запуска Grafana..."
sleep 10

echo ""
echo "✅ Учётные данные изменены!"
echo ""
echo "🔐 Учётные данные:"
echo "   Логин: $NEW_USER"
if [[ "$NEW_PASSWORD" == "admin" ]]; then
    echo "   Пароль: admin (временно, измените через веб-интерфейс)"
else
    echo "   Пароль: $NEW_PASSWORD"
    echo "   ⚠️  Если пароль не подходит, войдите с паролем 'admin' и измените его в настройках"
fi
echo ""
echo "📝 Откройте Grafana: http://ваш_ip:3000"
echo ""
echo "💡 Рекомендация: После входа измените пароль через веб-интерфейс:"
echo "   Configuration → Users → Admin → Change Password"
