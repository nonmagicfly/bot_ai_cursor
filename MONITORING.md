# Мониторинг Telegram бота с Prometheus и Grafana

Проект включает полноценную систему мониторинга на базе Prometheus и Grafana.

## Компоненты мониторинга

### 1. Prometheus метрики

Бот предоставляет метрики через HTTP endpoint на порту `8000`:

- **URL метрик**: `http://localhost:8000/metrics`
- **Health check**: `http://localhost:8000/health`

### 2. Доступные метрики

#### Метрики пользователей
- `bot_users_total` - Общее количество зарегистрированных пользователей
- `bot_users_active_today` - Количество активных пользователей за сегодня

#### Метрики операций
- `bot_operations_total{operation_type}` - Общее количество операций по типам
- `bot_operations_today{operation_type}` - Количество операций за сегодня по типам

Типы операций:
- `start` - Команда /start
- `newprogram` - Создание программы
- `startworkout` - Начало тренировки
- `programs` - Просмотр программ
- `report` - Просмотр отчётов
- `deleteall` - Удаление всех программ
- `save_record` - Сохранение записи тренировки

#### Метрики базы данных
- `bot_programs_total` - Общее количество программ
- `bot_programs_active` - Количество активных программ
- `bot_records_total` - Общее количество записей тренировок
- `bot_records_today` - Количество записей за сегодня

#### Метрики производительности
- `bot_request_duration_seconds{handler}` - Длительность обработки запросов
- `bot_request_errors_total{error_type}` - Количество ошибок

#### Метрики системы
- `bot_health` - Состояние бота (1 = работает, 0 = не работает)
- `bot_uptime_seconds` - Время работы бота в секундах
- `bot_system_cpu_percent` - Загрузка CPU в процентах
- `bot_system_memory_percent` - Использование памяти в процентах
- `bot_system_memory_bytes` - Использование памяти в байтах

## Запуск мониторинга

### С Docker Compose (рекомендуется)

1. Убедитесь, что в `.env` файле установлен `BOT_TOKEN`:
```bash
BOT_TOKEN=your_token_here
GRAFANA_PASSWORD=your_password_here  # Опционально, по умолчанию: admin
```

2. Запустите все сервисы:
```bash
docker-compose up -d
```

3. Доступ к сервисам:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (логин: `admin`, пароль: из переменной `GRAFANA_PASSWORD` или `admin`)
- **Метрики бота**: http://localhost:8000/metrics

### Ручной запуск

1. Запустите бота:
```bash
python bot.py
```

2. Запустите Prometheus:
```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus:latest
```

3. Запустите Grafana:
```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana:latest
```

## Настройка Grafana

### Автоматическая настройка

При использовании `docker-compose.yml`:
- Prometheus datasource настраивается автоматически
- Дашборд загружается автоматически (если настроен)

### Ручная настройка

1. Войдите в Grafana (http://localhost:3000)
2. Добавьте Prometheus как datasource:
   - URL: `http://prometheus:9090` (в Docker) или `http://localhost:9090` (локально)
   - Access: Server (default)
3. Импортируйте дашборд из файла `grafana/dashboards/telegram-bot-dashboard.json`

## Использование метрик

### Проверка доступности бота

```bash
curl http://localhost:8000/health
```

### Просмотр метрик

```bash
curl http://localhost:8000/metrics
```

### Запросы к Prometheus

Примеры запросов в Prometheus Query Language (PromQL):

```promql
# Количество пользователей
bot_users_total

# Активные пользователи за сегодня
bot_users_active_today

# Операции за сегодня по типам
bot_operations_today

# Загрузка CPU
bot_system_cpu_percent

# Использование памяти
bot_system_memory_percent

# Время работы бота
bot_uptime_seconds

# Количество ошибок
rate(bot_request_errors_total[5m])
```

## Алерты (опционально)

Вы можете настроить алерты в Prometheus для:
- Падения бота (`bot_health == 0`)
- Высокой загрузки CPU (`bot_system_cpu_percent > 80`)
- Высокого использования памяти (`bot_system_memory_percent > 90`)
- Большого количества ошибок (`rate(bot_request_errors_total[5m]) > 10`)

Пример конфигурации алертов в `prometheus.yml`:

```yaml
rule_files:
  - "alerts.yml"
```

## Структура файлов мониторинга

```
.
├── metrics.py              # Определение метрик Prometheus
├── metrics_server.py       # HTTP сервер для метрик
├── prometheus.yml          # Конфигурация Prometheus
├── docker-compose.yml      # Docker Compose с Prometheus и Grafana
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   │   └── prometheus.yml
    │   └── dashboards/
    │       └── dashboards.yml
    └── dashboards/
        └── telegram-bot-dashboard.json
```

## Обновление метрик

Метрики обновляются автоматически каждые 30 секунд. Вы можете изменить интервал в `bot.py`:

```python
await asyncio.sleep(30)  # Измените на нужный интервал
```

## Troubleshooting

### Метрики не отображаются

1. Проверьте, что бот запущен и доступен на порту 8000:
```bash
curl http://localhost:8000/metrics
```

2. Проверьте логи бота:
```bash
docker-compose logs telegram-bot
```

3. Проверьте конфигурацию Prometheus:
```bash
docker-compose logs prometheus
```

### Grafana не подключается к Prometheus

1. Убедитесь, что оба сервиса в одной сети Docker
2. Проверьте URL в настройках datasource: `http://prometheus:9090`
3. Проверьте логи Grafana:
```bash
docker-compose logs grafana
```

### Высокое использование ресурсов

Если мониторинг потребляет слишком много ресурсов:
- Увеличьте интервал сбора метрик в `prometheus.yml` (`scrape_interval`)
- Уменьшите время хранения данных в Prometheus
- Используйте более легкие образы (например, `prom/prometheus:latest` вместо полной версии)


