#!/bin/bash
# Скрипт для настройки firewall (UFW) на Ubuntu
# Открывает необходимые порты для бота и мониторинга

set -e

echo "🔥 Настройка firewall (UFW) для Telegram бота..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка, запущен ли скрипт от root или с sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠️  Скрипт требует прав администратора${NC}"
    echo "Запустите: sudo ./setup-firewall.sh"
    exit 1
fi

# Проверка наличия UFW
if ! command -v ufw &> /dev/null; then
    echo -e "${YELLOW}📦 UFW не установлен. Устанавливаю...${NC}"
    apt-get update
    apt-get install -y ufw
    echo -e "${GREEN}✅ UFW установлен${NC}"
fi

# Загрузка переменных из .env если есть
if [ -f .env ]; then
    source .env
fi

# Порты по умолчанию
SSH_PORT=22
METRICS_PORT=${METRICS_PORT:-8000}
PROMETHEUS_PORT=${PROMETHEUS_PORT:-9090}
GRAFANA_PORT=${GRAFANA_PORT:-3000}

echo ""
echo "📋 Порты для открытия:"
echo "   - SSH: $SSH_PORT (обязательно!)"
echo "   - Метрики бота: $METRICS_PORT"
echo "   - Prometheus: $PROMETHEUS_PORT"
echo "   - Grafana: $GRAFANA_PORT"
echo ""

# Функция для проверки, открыт ли порт
is_port_open() {
    local port=$1
    ufw status | grep -q "^$port" || ufw status | grep -q "$port/tcp"
}

# Функция для открытия порта
open_port() {
    local port=$1
    local description=$2
    
    if is_port_open "$port"; then
        echo -e "${GREEN}✅ Порт $port уже открыт ($description)${NC}"
    else
        echo -e "${YELLOW}🔓 Открываю порт $port ($description)...${NC}"
        ufw allow $port/tcp comment "$description"
        echo -e "${GREEN}✅ Порт $port открыт${NC}"
    fi
}

# Проверка статуса UFW
UFW_STATUS=$(ufw status | head -n 1)

if echo "$UFW_STATUS" | grep -q "inactive"; then
    echo -e "${YELLOW}⚠️  UFW неактивен${NC}"
    echo ""
    echo "🔒 ВАЖНО: Перед активацией UFW нужно открыть SSH порт!"
    echo "   Если вы сейчас подключены по SSH, не закрывайте соединение!"
    echo ""
    
    # Открываем SSH порт в первую очередь
    echo -e "${RED}🔓 Открываю SSH порт $SSH_PORT (критически важно!)...${NC}"
    ufw allow $SSH_PORT/tcp comment "SSH - обязательно оставить открытым"
    echo -e "${GREEN}✅ SSH порт открыт${NC}"
    echo ""
    
    # Открываем остальные порты
    open_port "$METRICS_PORT" "Bot metrics endpoint"
    open_port "$PROMETHEUS_PORT" "Prometheus monitoring"
    open_port "$GRAFANA_PORT" "Grafana dashboards"
    
    echo ""
    echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Сейчас будет активирован firewall!${NC}"
    echo "   Убедитесь, что SSH порт открыт (выше показано ✅)"
    echo ""
    read -p "Продолжить активацию firewall? (yes/no): " -r
    echo
    
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}🔥 Активирую UFW...${NC}"
        ufw --force enable
        echo -e "${GREEN}✅ Firewall активирован${NC}"
    else
        echo -e "${YELLOW}⚠️  Активация отменена. Firewall остаётся неактивным.${NC}"
        echo "   Для активации вручную выполните: sudo ufw enable"
        exit 0
    fi
else
    echo -e "${GREEN}✅ UFW уже активен${NC}"
    echo ""
    
    # Открываем все необходимые порты
    open_port "$SSH_PORT" "SSH"
    open_port "$METRICS_PORT" "Bot metrics endpoint"
    open_port "$PROMETHEUS_PORT" "Prometheus monitoring"
    open_port "$GRAFANA_PORT" "Grafana dashboards"
fi

echo ""
echo "📊 Текущий статус firewall:"
echo ""
ufw status numbered

echo ""
echo -e "${GREEN}✅ Настройка firewall завершена!${NC}"
echo ""
echo "📝 Полезные команды:"
echo "   Просмотр статуса: sudo ufw status"
echo "   Просмотр с номерами: sudo ufw status numbered"
echo "   Закрыть порт: sudo ufw delete allow <port>"
echo "   Закрыть по номеру: sudo ufw delete <номер>"
echo "   Отключить firewall: sudo ufw disable"
echo ""
echo -e "${YELLOW}🔒 Рекомендации по безопасности:${NC}"
echo "   1. Не открывайте порты мониторинга публично без необходимости"
echo "   2. Используйте SSH туннель для доступа к Grafana:"
echo "      ssh -L 3000:localhost:3000 user@server"
echo "   3. Рассмотрите использование VPN для доступа к мониторингу"
echo "   4. Регулярно проверяйте открытые порты: sudo ufw status"
echo ""

