# Развёртывание на VPS с мониторингом

Полная инструкция по развёртыванию Telegram бота на VPS с системой мониторинга Prometheus + Grafana.

## Быстрый старт

### 1. Подключитесь к VPS

```bash
ssh user@your-server-ip
```

### 2. Клонируйте репозиторий

```bash
git clone https://github.com/nonmagicfly/bot_ai_cursor.git
cd bot_ai_cursor
```

### 3. Настройте переменные окружения

```bash
# Создайте .env файл
cp env.example .env
nano .env
```

Минимальная конфигурация:
```env
BOT_TOKEN=ваш_токен_бота
DATABASE=./data/gym.db
```

Для включения мониторинга:
```env
BOT_TOKEN=ваш_токен_бота
DATABASE=./data/gym.db
ENABLE_MONITORING=true
GRAFANA_PASSWORD=ваш_безопасный_пароль
METRICS_PORT=8000
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

### 4. Запустите деплой

```bash
# Сделайте скрипт исполняемым
chmod +x deploy.sh

# Запустите деплой
./deploy.sh
```

Скрипт автоматически:
- Проверит и установит Docker (если нужно)
- Проверит и установит Docker Compose (если нужно)
- Соберёт и запустит контейнеры
- Если `ENABLE_MONITORING=true`, запустит Prometheus и Grafana

## Варианты запуска

### Вариант 1: Только бот (без мониторинга)

```bash
# В .env установите
ENABLE_MONITORING=false

# Запуск
docker-compose up -d
```

### Вариант 2: Бот + мониторинг (рекомендуется)

```bash
# В .env установите
ENABLE_MONITORING=true

# Запуск
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Вариант 3: Добавить мониторинг к уже работающему боту

```bash
# Бот уже запущен, добавляем мониторинг
chmod +x deploy-monitoring.sh
./deploy-monitoring.sh
```

## Проверка работы

### Проверка бота

```bash
# Проверка метрик
curl http://localhost:8000/health
# Должен вернуть: OK

# Просмотр метрик
curl http://localhost:8000/metrics
```

### Проверка Prometheus

```bash
# Откройте в браузере
http://ваш_ip:9090

# Или через curl
curl http://localhost:9090/-/healthy
```

### Проверка Grafana

```bash
# Откройте в браузере
http://ваш_ip:3000

# Логин: admin
# Пароль: из переменной GRAFANA_PASSWORD в .env
```

## Управление сервисами

### Просмотр статуса

```bash
# Все сервисы
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml ps

# Только бот
docker-compose ps
```

### Просмотр логов

```bash
# Все сервисы
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f

# Только бот
docker-compose logs -f telegram-bot

# Только Prometheus
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f prometheus

# Только Grafana
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f grafana
```

### Перезапуск

```bash
# Все сервисы
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml restart

# Только бот
docker-compose restart telegram-bot

# Только мониторинг
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml restart prometheus grafana
```

### Остановка

```bash
# Все сервисы
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml down

# Только мониторинг (бот продолжит работать)
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml stop prometheus grafana

# Только бот
docker-compose down
```

## Настройка файрвола

### UFW (Ubuntu)

```bash
# Разрешить SSH (важно сделать первым!)
sudo ufw allow 22/tcp

# Порт для метрик бота (опционально, для внешнего доступа)
sudo ufw allow 8000/tcp

# Порт Prometheus (опционально, для внешнего доступа)
sudo ufw allow 9090/tcp

# Порт Grafana (опционально, для внешнего доступа)
sudo ufw allow 3000/tcp

# Включить файрвол
sudo ufw enable

# Проверить статус
sudo ufw status
```

### Firewalld (CentOS/RHEL)

```bash
# Разрешить SSH
sudo firewall-cmd --permanent --add-service=ssh

# Разрешить порты
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=9090/tcp
sudo firewall-cmd --permanent --add-port=3000/tcp

# Применить изменения
sudo firewall-cmd --reload
```

## Безопасность

### Рекомендации

1. **Не открывайте порты мониторинга публично** - используйте VPN или SSH туннель
2. **Используйте сильный пароль для Grafana**
3. **Настройте reverse proxy (nginx)** с аутентификацией
4. **Ограничьте доступ по IP** в файрволе

### SSH туннель для доступа к Grafana

```bash
# На вашем локальном компьютере
ssh -L 3000:localhost:3000 user@your-server-ip

# Затем откройте в браузере
http://localhost:3000
```

### Настройка nginx с аутентификацией (опционально)

Создайте `/etc/nginx/sites-available/monitoring`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /grafana/ {
        proxy_pass http://localhost:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /prometheus/ {
        proxy_pass http://localhost:9090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Обновление

### Обновление бота

```bash
cd bot_ai_cursor
git pull
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml build telegram-bot
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d telegram-bot
```

### Обновление Prometheus и Grafana

```bash
# Обновление образов
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml pull prometheus grafana

# Перезапуск
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d prometheus grafana
```

## Резервное копирование

### База данных

```bash
# Создание бэкапа
docker-compose exec telegram-bot cp /app/data/gym.db /app/data/gym.db.backup

# Или с хоста
cp data/gym.db data/gym.db.backup
```

### Данные Prometheus и Grafana

```bash
# Бэкап volumes
docker run --rm \
  -v bot_ai_cursor_prometheus-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/prometheus-backup.tar.gz /data

docker run --rm \
  -v bot_ai_cursor_grafana-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/grafana-backup.tar.gz /data
```

## Troubleshooting

### Бот не запускается

```bash
# Проверьте логи
docker-compose logs telegram-bot

# Проверьте переменные окружения
docker-compose exec telegram-bot env | grep BOT_TOKEN
```

### Prometheus не собирает метрики

```bash
# Проверьте доступность бота
curl http://localhost:8000/metrics

# Проверьте конфигурацию Prometheus
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml

# Проверьте логи
docker-compose logs prometheus
```

### Grafana не подключается к Prometheus

1. Проверьте, что оба сервиса запущены:
   ```bash
   docker-compose ps
   ```

2. Проверьте настройки datasource в Grafana (должен быть `http://prometheus:9090`)

3. Проверьте сеть Docker:
   ```bash
   docker network ls
   docker network inspect bot_ai_cursor_monitoring
   ```

## Дополнительная документация

- 📖 [MONITORING.md](MONITORING.md) - Подробная документация по мониторингу
- 📖 [QUICKSTART_MONITORING.md](QUICKSTART_MONITORING.md) - Быстрый старт мониторинга
- 📖 [deploy-ubuntu.md](deploy-ubuntu.md) - Общая инструкция по деплою


