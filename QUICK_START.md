# 🚀 Быстрый старт: Запуск бота и настройка firewall

## Шаг 1: Обновление репозитория

Если репозиторий уже клонирован:

```bash
cd ~/bot_ai_cursor
git pull origin main
```

Если репозиторий ещё не клонирован:

```bash
cd ~
git clone https://github.com/nonmagicfly/bot_ai_cursor.git
cd bot_ai_cursor
```

## Шаг 2: Настройка переменных окружения

```bash
# Создайте .env файл (если его нет)
cp env.example .env

# Отредактируйте .env файл
nano .env
```

**Минимальная конфигурация для запуска с мониторингом:**

```env
BOT_TOKEN=ваш_токен_бота_здесь
DATABASE=./data/gym.db
ENABLE_MONITORING=true
METRICS_PORT=8000
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_USER=admin
GRAFANA_PASSWORD=ваш_безопасный_пароль
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

## Шаг 3: Настройка Firewall (UFW)

### Автоматическая настройка (рекомендуется):

```bash
chmod +x setup-firewall.sh
sudo ./setup-firewall.sh
```

Скрипт автоматически:
- Установит UFW (если не установлен)
- Откроет SSH порт (22) - критически важно!
- Откроет порты мониторинга (8000, 9090, 3000)
- Активирует firewall

### Ручная настройка:

```bash
# Установка UFW (если не установлен)
sudo apt update
sudo apt install -y ufw

# Открытие SSH порта (ВАЖНО сделать первым!)
sudo ufw allow 22/tcp

# Открытие портов мониторинга
sudo ufw allow 8000/tcp comment "Bot metrics"
sudo ufw allow 9090/tcp comment "Prometheus"
sudo ufw allow 3000/tcp comment "Grafana"

# Активирование firewall
sudo ufw enable

# Проверка статуса
sudo ufw status
```

## Шаг 4: Запуск бота с мониторингом

### Автоматический запуск (рекомендуется):

```bash
chmod +x deploy-with-monitoring.sh
./deploy-with-monitoring.sh
```

### Ручной запуск:

```bash
# Сборка образов
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml build

# Запуск всех сервисов
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## Шаг 5: Проверка работы

### Проверка статуса контейнеров:

```bash
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml ps
```

### Проверка логов:

```bash
# Все сервисы
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f

# Только бот
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f telegram-bot
```

### Проверка доступности:

```bash
# Health check бота
curl http://localhost:8000/health

# Метрики бота
curl http://localhost:8000/metrics

# Prometheus (в браузере)
# http://ваш_ip:9090

# Grafana (в браузере)
# http://ваш_ip:3000
```

## Полезные команды

### Управление контейнерами:

```bash
# Остановка
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml down

# Перезапуск
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml restart

# Пересборка после изменений
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml build
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Управление firewall:

```bash
# Просмотр статуса
sudo ufw status

# Просмотр с номерами правил
sudo ufw status numbered

# Закрыть порт (по номеру)
sudo ufw delete <номер>

# Отключить firewall (не рекомендуется)
sudo ufw disable
```

### Обновление бота:

```bash
# Обновить код из репозитория
git pull origin main

# Пересобрать и перезапустить
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml build
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## Troubleshooting

### Бот не запускается:

```bash
# Проверьте логи
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs telegram-bot

# Проверьте .env файл
cat .env | grep BOT_TOKEN
```

### Проблемы с firewall:

```bash
# Проверьте статус
sudo ufw status verbose

# Проверьте, что порты открыты
sudo ufw status | grep -E "(8000|9090|3000|22)"
```

### Проблемы с Docker:

```bash
# Проверьте статус Docker
sudo systemctl status docker

# Перезапустите Docker
sudo systemctl restart docker
```

## Безопасность

⚠️ **Важные рекомендации:**

1. **Не открывайте порты мониторинга публично** без необходимости
2. Используйте **SSH туннель** для доступа к Grafana:
   ```bash
   ssh -L 3000:localhost:3000 user@your-server-ip
   ```
   Затем откройте в браузере: `http://localhost:3000`

3. Используйте **сильный пароль** для Grafana
4. Рассмотрите использование **VPN** для доступа к мониторингу

## Полная документация

- 📖 [DEPLOY_NOW.md](DEPLOY_NOW.md) - Подробная инструкция по развёртыванию
- 📖 [VPS_DEPLOYMENT.md](VPS_DEPLOYMENT.md) - Развёртывание на VPS
- 📖 [MONITORING.md](MONITORING.md) - Документация по мониторингу
- 📖 [deploy-ubuntu.md](deploy-ubuntu.md) - Общая инструкция

