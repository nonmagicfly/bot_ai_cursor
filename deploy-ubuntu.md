# Развёртывание Docker контейнера на Ubuntu сервере

## Быстрый старт

### Вариант 1: Автоматический деплой (рекомендуется)

1. **Клонируйте репозиторий на сервер:**
```bash
git clone https://github.com/nonmagicfly/bot_ai_cursor.git
cd bot_ai_cursor
```

2. **Сделайте скрипт исполняемым и запустите:**
```bash
chmod +x deploy.sh
./deploy.sh
```

Скрипт автоматически:
- Проверит и установит Docker (если нужно)
- Проверит и установит Docker Compose (если нужно)
- Создаст `.env` файл из примера
- Соберёт и запустит контейнер

### Вариант 2: Ручной деплой

#### Шаг 1: Установка Docker

**⚠️ Если Docker уже установлен и работает нормально, пропустите этот шаг.**

**Если у вас проблемы с Docker или нужна чистая переустановка:**

1. **Полное удаление старой версии Docker (если нужно):**
```bash
# Используйте скрипт для полного удаления
chmod +x cleanup-docker.sh
sudo ./cleanup-docker.sh
```

Или вручную:
```bash
# Остановка всех контейнеров
sudo docker stop $(sudo docker ps -aq) 2>/dev/null || true
sudo docker rm $(sudo docker ps -aq) 2>/dev/null || true

# Удаление Docker
sudo apt-get remove -y docker docker-engine docker.io containerd runc
sudo apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo rm -rf /var/lib/docker
sudo rm -rf /var/lib/containerd
sudo rm -rf /etc/docker
```

2. **Установка Docker:**

```bash
# Обновление пакетов
sudo apt update

# Установка зависимостей
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Добавление официального GPG ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавление репозитория Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Добавление пользователя в группу docker (чтобы не использовать sudo)
sudo usermod -aG docker $USER

# Перезагрузка сессии (или выполните: newgrp docker)
```

#### Шаг 2: Установка Docker Compose (если не установлен)

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Шаг 3: Клонирование репозитория

```bash
git clone https://github.com/nonmagicfly/bot_ai_cursor.git
cd bot_ai_cursor
```

#### Шаг 4: Настройка переменных окружения

```bash
# Создание .env файла из примера
cp env.example .env

# Редактирование .env файла
nano .env
```

Добавьте ваш токен бота:
```
BOT_TOKEN=ваш_токен_бота_здесь
DATABASE=./data/gym.db
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

#### Шаг 5: Создание папки для данных

```bash
mkdir -p data
```

#### Шаг 6: Настройка мониторинга (опционально)

Если хотите включить мониторинг (Prometheus + Grafana), отредактируйте `.env`:

```bash
nano .env
```

Добавьте или измените:
```env
ENABLE_MONITORING=true
GRAFANA_PASSWORD=ваш_безопасный_пароль
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
METRICS_PORT=8000
```

#### Шаг 7: Сборка и запуск контейнера

**Вариант A: Только бот (без мониторинга)**

```bash
# Сборка образа
docker-compose build

# Запуск в фоновом режиме
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

**Вариант B: Бот + мониторинг**

```bash
# Сборка образов
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml build

# Запуск всех сервисов
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Просмотр логов
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f
```

**Вариант C: Использование скрипта deploy.sh (автоматически определяет мониторинг)**

```bash
# Если ENABLE_MONITORING=true в .env, запустит с мониторингом
./deploy.sh
```

**Или с использованием Docker напрямую:**

```bash
# Сборка образа
docker build -t telegram-workout-bot .

# Запуск контейнера
docker run -d \
  --name telegram-workout-bot \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  telegram-workout-bot
```

## Управление ботом

### Просмотр логов

```bash
# Только бот
docker-compose logs -f

# Бот + мониторинг
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml logs -f

# Только бот (Docker)
docker logs -f telegram-workout-bot
```

### Остановка бота

```bash
# Только бот
docker-compose down

# Бот + мониторинг
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml down

# Только бот (Docker)
docker stop telegram-workout-bot
docker rm telegram-workout-bot
```

### Перезапуск бота

```bash
# С Docker Compose
docker-compose restart

# С Docker
docker restart telegram-workout-bot
```

### Обновление бота

```bash
# Перейти в директорию проекта
cd bot_ai_cursor

# Получить последние изменения
git pull

# Пересобрать и перезапустить
docker-compose down
docker-compose build
docker-compose up -d
```

### Проверка статуса

```bash
# С Docker Compose
docker-compose ps

# С Docker
docker ps | grep telegram-workout-bot
```

## Автозапуск при перезагрузке сервера

Docker Compose и Docker автоматически перезапускают контейнеры при перезагрузке благодаря флагу `restart: unless-stopped` в `docker-compose.yml`.

Если используете Docker напрямую, убедитесь, что контейнер запущен с флагом `--restart unless-stopped`.

## Резервное копирование базы данных

База данных хранится в папке `./data/gym.db` на хосте (благодаря volume в docker-compose.yml).

Для резервного копирования:

```bash
# Создание резервной копии
cp data/gym.db data/gym.db.backup.$(date +%Y%m%d_%H%M%S)

# Восстановление из резервной копии
cp data/gym.db.backup.20240101_120000 data/gym.db
docker-compose restart
```

## Устранение проблем

### Бот не запускается

1. Проверьте логи:
```bash
docker-compose logs
```

2. Проверьте переменные окружения:
```bash
cat .env
```

3. Убедитесь, что `BOT_TOKEN` установлен и корректен.

### Ошибка "Permission denied"

Если получаете ошибку доступа к Docker:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Ошибка "Port already in use"

Если порт занят (маловероятно для этого бота, но на всякий случай):
```bash
# Проверка занятых портов
sudo netstat -tulpn | grep LISTEN
```

### Пересоздание контейнера с нуля

```bash
# Остановка и удаление контейнера и образа
docker-compose down
docker rmi telegram-workout-bot 2>/dev/null || true

# Удаление базы данных (опционально)
rm -f data/gym.db

# Пересборка и запуск
docker-compose build
docker-compose up -d
```

### Полное удаление и переустановка Docker

Если у вас серьёзные проблемы с Docker (конфликты версий, ошибки установки, повреждённые данные), может потребоваться полная переустановка:

**⚠️ ВНИМАНИЕ: Это удалит ВСЕ контейнеры, образы и данные Docker!**

1. **Используйте автоматический скрипт (рекомендуется):**
```bash
chmod +x cleanup-docker.sh
sudo ./cleanup-docker.sh
```

2. **Или удалите вручную:**
```bash
# Остановка всех контейнеров
sudo docker stop $(sudo docker ps -aq) 2>/dev/null || true
sudo docker rm $(sudo docker ps -aq) 2>/dev/null || true

# Удаление всех образов
sudo docker rmi $(sudo docker images -q) 2>/dev/null || true

# Удаление всех volumes
sudo docker volume rm $(sudo docker volume ls -q) 2>/dev/null || true

# Полная очистка системы
sudo docker system prune -a --volumes -f

# Удаление пакетов Docker
sudo apt-get remove -y docker docker-engine docker.io containerd runc
sudo apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Удаление данных и конфигурации
sudo rm -rf /var/lib/docker
sudo rm -rf /var/lib/containerd
sudo rm -rf /etc/docker
sudo rm -f /usr/local/bin/docker-compose

# Очистка зависимостей
sudo apt-get autoremove -y
sudo apt-get autoclean
```

3. **После удаления перезагрузите систему (рекомендуется):**
```bash
sudo reboot
```

4. **Затем установите Docker заново:**
```bash
# Используйте скрипт развёртывания
./deploy.sh

# Или установите вручную (см. раздел "Установка Docker" выше)
```

**Когда нужно полное удаление:**
- Конфликты версий Docker
- Ошибки при установке обновлений
- Повреждённые данные Docker
- Необходимость чистой установки
- Переход с одной версии Docker на другую

## Мониторинг

### Использование ресурсов

```bash
docker stats telegram-workout-bot
```

### Размер образа

```bash
docker images | grep telegram-workout-bot
```

## Безопасность

1. **Не коммитьте `.env` файл в Git** (он уже в `.gitignore`)
2. **Используйте сильные пароли** для доступа к серверу
3. **Настройте firewall** (UFW):
```bash
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```
4. **Регулярно обновляйте систему:**
```bash
sudo apt update && sudo apt upgrade -y
```

