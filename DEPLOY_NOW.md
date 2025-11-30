# 🚀 Инструкция по развёртыванию с мониторингом (Вариант 2)

## Текущий статус

✅ Файл `.env` настроен с `ENABLE_MONITORING=true`
✅ Все конфигурационные файлы готовы
✅ Скрипты развёртывания созданы

## Варианты развёртывания

### Вариант A: На VPS сервере (Ubuntu/Debian)

1. **Подключитесь к VPS:**
```bash
ssh user@your-server-ip
```

2. **Клонируйте репозиторий (или обновите существующий):**

**Если репозиторий ещё не клонирован:**
```bash
git clone https://github.com/nonmagicfly/bot_ai_cursor.git
cd bot_ai_cursor
```

**Если репозиторий уже существует:**
```bash
cd bot_ai_cursor
chmod +x update-repo.sh
./update-repo.sh
```

Или вручную:
```bash
cd bot_ai_cursor
git pull origin main
```

3. **Настройте .env файл:**
```bash
cp env.example .env
nano .env
```

Убедитесь, что установлено:
```env
BOT_TOKEN=ваш_токен_бота
ENABLE_MONITORING=true
GRAFANA_PASSWORD=ваш_безопасный_пароль
```

4. **Запустите развёртывание:**
```bash
chmod +x deploy-with-monitoring.sh
./deploy-with-monitoring.sh
```

Или вручную:
```bash
# Сборка
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml build

# Запуск
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Вариант B: Локально (если установлен Docker)

На Windows с Docker Desktop:

```powershell
# Проверка Docker
docker --version
docker-compose --version

# Запуск
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## Проверка работы

### 1. Проверка бота

```bash
# Health check
curl http://localhost:8000/health

# Метрики
curl http://localhost:8000/metrics
```

### 2. Проверка Prometheus

Откройте в браузере: `http://localhost:9090` (или IP вашего сервера)

Попробуйте запрос: `bot_health`

### 3. Проверка Grafana

Откройте в браузере: `http://localhost:3000` (или IP вашего сервера)

- Логин: `admin`
- Пароль: из переменной `GRAFANA_PASSWORD` в `.env`

## Управление

### Просмотр логов

```bash
# Все сервисы
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f

# Только бот
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f telegram-bot

# Только Prometheus
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f prometheus

# Только Grafana
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f grafana
```

### Статус сервисов

```bash
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml ps
```

### Перезапуск

```bash
# Все сервисы
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml restart

# Только бот
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml restart telegram-bot
```

### Остановка

```bash
# Все сервисы
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml down

# Только мониторинг (бот продолжит работать)
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml stop prometheus grafana
```

## Порты

По умолчанию используются следующие порты:

- **8000** - Метрики бота (HTTP endpoint)
- **9090** - Prometheus Web UI
- **3000** - Grafana Web UI

Вы можете изменить их в файле `.env`:
```env
METRICS_PORT=8000
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

## Настройка файрвола (на VPS)

### Автоматическая настройка (рекомендуется)

Используйте готовый скрипт для настройки UFW:

```bash
chmod +x setup-firewall.sh
sudo ./setup-firewall.sh
```

Скрипт автоматически:
- Проверит наличие UFW и установит при необходимости
- Откроет SSH порт (22) - критически важно!
- Откроет порты мониторинга (8000, 9090, 3000)
- Активирует firewall с подтверждением
- Покажет текущий статус

### Ручная настройка

Если используете UFW вручную:

```bash
# Разрешить SSH (важно!)
sudo ufw allow 22/tcp

# Порты мониторинга (опционально, для внешнего доступа)
sudo ufw allow 8000/tcp
sudo ufw allow 9090/tcp
sudo ufw allow 3000/tcp

# Включить файрвол
sudo ufw enable
```

**Важно:** Для безопасности рекомендуется не открывать порты мониторинга публично. Используйте SSH туннель или VPN.

## Troubleshooting

### Бот не запускается

```bash
# Проверьте логи
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs telegram-bot

# Проверьте переменные окружения
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml exec telegram-bot env | grep BOT_TOKEN
```

### Prometheus не собирает метрики

```bash
# Проверьте доступность бота
curl http://localhost:8000/metrics

# Проверьте конфигурацию
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml exec prometheus cat /etc/prometheus/prometheus.yml
```

### Grafana не подключается к Prometheus

1. Проверьте, что оба сервиса запущены
2. В Grafana: Configuration → Data Sources → Prometheus
3. URL должен быть: `http://prometheus:9090`

### Проблемы с Docker

#### Docker не работает или ошибки установки

Если у вас проблемы с Docker (конфликты версий, ошибки установки), может потребоваться полная переустановка:

**⚠️ ВНИМАНИЕ: Это удалит ВСЕ контейнеры, образы и данные Docker!**

```bash
# Полное удаление Docker
chmod +x cleanup-docker.sh
sudo ./cleanup-docker.sh

# После удаления перезагрузите систему (рекомендуется)
sudo reboot

# Затем установите Docker заново
./deploy-with-monitoring.sh
```

#### Нет доступа к Docker

```bash
# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER

# Активируйте группу
newgrp docker

# Проверьте доступ
docker ps
```

## Дополнительная документация

- 📖 [VPS_DEPLOYMENT.md](VPS_DEPLOYMENT.md) - Подробная инструкция для VPS
- 📖 [MONITORING.md](MONITORING.md) - Документация по мониторингу
- 📖 [deploy-ubuntu.md](deploy-ubuntu.md) - Общая инструкция по деплою


