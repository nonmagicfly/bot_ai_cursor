#!/bin/bash
# Скрипт для полного удаления Docker и Docker Compose
# Используйте только если нужно полностью переустановить Docker

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}⚠️  ВНИМАНИЕ: Этот скрипт полностью удалит Docker!${NC}"
echo ""
echo "Будет удалено:"
echo "  - Все контейнеры (остановленные и запущенные)"
echo "  - Все образы"
echo "  - Все volumes (данные контейнеров)"
echo "  - Все networks"
echo "  - Docker Engine"
echo "  - Docker Compose"
echo "  - Все конфигурационные файлы"
echo ""
echo -e "${YELLOW}⚠️  ВСЕ ДАННЫЕ БУДУТ УДАЛЕНЫ!${NC}"
echo ""
read -p "Вы уверены, что хотите продолжить? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Отмена. Docker не был удалён."
    exit 0
fi

# Проверка, запущен ли скрипт от root или с sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠️  Скрипт требует прав администратора${NC}"
    echo "Запустите: sudo ./cleanup-docker.sh"
    exit 1
fi

echo ""
echo -e "${YELLOW}🛑 Останавливаю все контейнеры...${NC}"
# Остановка всех контейнеров
docker stop $(docker ps -aq) 2>/dev/null || true

echo -e "${YELLOW}🗑️  Удаляю все контейнеры...${NC}"
# Удаление всех контейнеров
docker rm $(docker ps -aq) 2>/dev/null || true

echo -e "${YELLOW}🗑️  Удаляю все образы...${NC}"
# Удаление всех образов
docker rmi $(docker images -q) 2>/dev/null || true

echo -e "${YELLOW}🗑️  Удаляю все volumes...${NC}"
# Удаление всех volumes
docker volume rm $(docker volume ls -q) 2>/dev/null || true

echo -e "${YELLOW}🗑️  Удаляю все networks (кроме стандартных)...${NC}"
# Удаление всех пользовательских networks
docker network prune -f 2>/dev/null || true

echo -e "${YELLOW}🧹 Очищаю систему Docker...${NC}"
# Полная очистка системы
docker system prune -a --volumes -f 2>/dev/null || true

echo -e "${YELLOW}📦 Удаляю пакеты Docker...${NC}"

# Определение дистрибутива
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Не удалось определить дистрибутив"
    exit 1
fi

# Удаление Docker в зависимости от дистрибутива
case $OS in
    ubuntu|debian)
        echo "Обнаружен Ubuntu/Debian"
        apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
        apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>/dev/null || true
        ;;
    centos|rhel|fedora)
        echo "Обнаружен CentOS/RHEL/Fedora"
        yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine 2>/dev/null || true
        yum remove -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>/dev/null || true
        ;;
    *)
        echo "Дистрибутив не поддерживается автоматически"
        echo "Удалите Docker вручную"
        ;;
esac

echo -e "${YELLOW}🗑️  Удаляю конфигурационные файлы...${NC}"
# Удаление конфигурационных файлов и данных
rm -rf /var/lib/docker 2>/dev/null || true
rm -rf /var/lib/containerd 2>/dev/null || true
rm -rf /etc/docker 2>/dev/null || true
rm -rf ~/.docker 2>/dev/null || true

echo -e "${YELLOW}🗑️  Удаляю Docker Compose...${NC}"
# Удаление Docker Compose
rm -f /usr/local/bin/docker-compose 2>/dev/null || true
rm -f /usr/bin/docker-compose 2>/dev/null || true

echo -e "${YELLOW}🧹 Очищаю зависимости...${NC}"
# Очистка неиспользуемых пакетов
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt-get autoremove -y 2>/dev/null || true
    apt-get autoclean 2>/dev/null || true
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
    yum autoremove -y 2>/dev/null || true
    yum clean all 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}✅ Docker полностью удалён!${NC}"
echo ""
echo "📝 Следующие шаги:"
echo "   1. Перезагрузите систему (рекомендуется):"
echo "      sudo reboot"
echo ""
echo "   2. Или запустите скрипт развёртывания для установки новой версии:"
echo "      ./deploy.sh"
echo "      или"
echo "      ./deploy-with-monitoring.sh"
echo ""
echo "   3. После установки активируйте группу docker:"
echo "      newgrp docker"
echo ""

