# 🚀 Полная переустановка на VPS

Инструкция по полной очистке и переустановке бота с мониторингом на VPS.

## Шаг 1: Полная очистка

### Автоматическая очистка (рекомендуется)

```bash
cd ~/bot_ai_cursor
chmod +x cleanup-all.sh
sudo ./cleanup-all.sh
```

Скрипт удалит:
- Все Docker контейнеры
- Все Docker образы
- Все Docker volumes (данные)
- Локальную базу данных бота
- Опционально: .env файл

### Ручная очистка

```bash
# 1. Остановите все контейнеры
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml down

# 2. Удалите все контейнеры
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

# 3. Удалите все образы
docker rmi $(docker images -q) 2>/dev/null || true

# 4. Удалите все volumes
docker volume rm $(docker volume ls -q) 2>/dev/null || true

# 5. Очистите систему
docker system prune -a --volumes -f

# 6. Удалите локальные данные
rm -rf data
rm -f .env  # Опционально
```

## Шаг 2: Обновление репозитория

```bash
cd ~/bot_ai_cursor

# Если репозиторий уже есть, обновите его
git pull origin main

# Если репозитория нет, клонируйте заново
cd ~
rm -rf bot_ai_cursor  # Если папка существует
git clone https://github.com/nonmagicfly/bot_ai_cursor.git
cd bot_ai_cursor
```

## Шаг 3: Настройка переменных окружения

```bash
# Создайте .env файл
cp env.example .env

# Отредактируйте .env
nano .env
```

**Минимальная конфигурация:**

```env
# Токен бота (обязательно!)
BOT_TOKEN=ваш_токен_бота_здесь

# База данных
DATABASE=./data/gym.db

# Мониторинг
ENABLE_MONITORING=true

# Порты
METRICS_PORT=8000
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Учётные данные Grafana
GRAFANA_USER=admin
GRAFANA_PASSWORD=ваш_безопасный_пароль

# URL Grafana
GRAFANA_ROOT_URL=http://ваш_ip:3000
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

## Шаг 4: Настройка Firewall

```bash
# Автоматическая настройка
chmod +x setup-firewall.sh
sudo ./setup-firewall.sh
```

Или вручную:
```bash
sudo apt update
sudo apt install -y ufw
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 9090/tcp
sudo ufw allow 3000/tcp
sudo ufw enable
```

## Шаг 5: Запуск бота с мониторингом

### Автоматический запуск (рекомендуется)

```bash
chmod +x deploy-with-monitoring.sh
./deploy-with-monitoring.sh
```

### Ручной запуск

```bash
# Сборка образов
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml build

# Запуск всех сервисов
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## Шаг 6: Проверка работы

### Проверка статуса

```bash
# Статус всех контейнеров
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml ps

# Должны быть запущены:
# - telegram-workout-bot (healthy)
# - prometheus (healthy)
# - grafana (healthy)
```

### Проверка логов

```bash
# Логи бота
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f telegram-bot

# Логи всех сервисов
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f
```

### Проверка доступности

```bash
# Health check бота
curl http://localhost:8000/health

# Метрики бота
curl http://localhost:8000/metrics

# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3000/api/health
```

### Проверка в браузере

- **Prometheus**: `http://ваш_ip:9090`
- **Grafana**: `http://ваш_ip:3000`
  - Логин: из `GRAFANA_USER` в `.env`
  - Пароль: из `GRAFANA_PASSWORD` в `.env`

## Troubleshooting

### Бот не запускается

```bash
# Проверьте логи
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs telegram-bot

# Проверьте .env файл
cat .env | grep BOT_TOKEN

# Убедитесь, что BOT_TOKEN установлен
```

### Prometheus не собирает метрики

```bash
# Проверьте доступность бота
curl http://localhost:8000/metrics

# Проверьте конфигурацию Prometheus
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml exec prometheus cat /etc/prometheus/prometheus.yml
```

### Grafana не подключается к Prometheus

1. Проверьте, что оба сервиса запущены
2. В Grafana: Configuration → Data Sources → Prometheus
3. URL должен быть: `http://prometheus:9090`

### Проблемы с Docker

```bash
# Проверьте статус Docker
sudo systemctl status docker

# Перезапустите Docker
sudo systemctl restart docker
```

## Полезные команды

### Управление контейнерами

```bash
# Остановка
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml down

# Перезапуск
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml restart

# Просмотр логов
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f

# Статус
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml ps
```

### Обновление бота

```bash
# Обновить код
git pull origin main

# Пересобрать и перезапустить
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml build
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## Дополнительная документация

- 📖 [QUICK_START.md](QUICK_START.md) - Быстрый старт
- 📖 [DEPLOY_NOW.md](DEPLOY_NOW.md) - Подробная инструкция по развёртыванию
- 📖 [VPS_DEPLOYMENT.md](VPS_DEPLOYMENT.md) - Развёртывание на VPS
- 📖 [MONITORING.md](MONITORING.md) - Документация по мониторингу

