#!/bin/bash
# Скрипт для полной очистки всех данных бота и мониторинга с VPS

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}⚠️  ВНИМАНИЕ: Этот скрипт полностью удалит ВСЕ данные!${NC}"
echo ""
echo "Будет удалено:"
echo "  - Все Docker контейнеры (бот, Prometheus, Grafana)"
echo "  - Все Docker образы"
echo "  - Все Docker volumes (базы данных, данные Grafana/Prometheus)"
echo "  - Все Docker networks"
echo "  - Локальная база данных бота (если есть)"
echo ""
echo -e "${YELLOW}⚠️  ВСЕ ДАННЫЕ БУДУТ БЕЗВОЗВРАТНО УДАЛЕНЫ!${NC}"
echo ""
read -p "Вы уверены, что хотите продолжить? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Отмена. Данные не были удалены."
    exit 0
fi

# Проверка, запущен ли скрипт от root или с sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠️  Некоторые операции требуют прав администратора${NC}"
    echo "Запустите: sudo ./cleanup-all.sh"
    echo "Или выполните команды вручную"
fi

echo ""
echo -e "${YELLOW}🛑 Останавливаю все контейнеры...${NC}"

# Остановка всех контейнеров проекта
if [ -f docker-compose.yml ]; then
    docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml down 2>/dev/null || true
    docker-compose down 2>/dev/null || true
fi

# Остановка всех контейнеров (на всякий случай)
docker stop $(docker ps -aq) 2>/dev/null || true

echo -e "${YELLOW}🗑️  Удаляю все контейнеры...${NC}"
docker rm $(docker ps -aq) 2>/dev/null || true

echo -e "${YELLOW}🗑️  Удаляю все образы...${NC}"
docker rmi $(docker images -q) 2>/dev/null || true

echo -e "${YELLOW}🗑️  Удаляю все volumes...${NC}"
docker volume rm $(docker volume ls -q) 2>/dev/null || true

echo -e "${YELLOW}🗑️  Удаляю все networks (кроме стандартных)...${NC}"
docker network prune -f 2>/dev/null || true

echo -e "${YELLOW}🧹 Очищаю систему Docker...${NC}"
docker system prune -a --volumes -f 2>/dev/null || true

echo -e "${YELLOW}🗑️  Удаляю локальные данные бота...${NC}"
# Удаление папки data (база данных)
if [ -d "data" ]; then
    rm -rf data
    echo "✅ Папка data удалена"
fi

# Удаление .env файла (опционально, можно закомментировать)
read -p "Удалить .env файл? (yes/no): " -r
echo
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    if [ -f .env ]; then
        rm -f .env
        echo "✅ Файл .env удалён"
    fi
fi

echo ""
echo -e "${GREEN}✅ Полная очистка завершена!${NC}"
echo ""
echo "📝 Следующие шаги:"
echo "   1. Если хотите переустановить всё заново:"
echo "      git pull origin main"
echo "      cp env.example .env"
echo "      nano .env  # Настройте BOT_TOKEN и другие параметры"
echo "      ./deploy-with-monitoring.sh"
echo ""
echo "   2. Или следуйте инструкциям в QUICK_START.md"
echo ""

