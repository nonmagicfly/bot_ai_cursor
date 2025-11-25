# Инструкция по развёртыванию бота на удалённом сервере

## Варианты размещения

### 1. VPS (Virtual Private Server) - Рекомендуется
- **DigitalOcean**: https://www.digitalocean.com (от $4/месяц)
- **Hetzner**: https://www.hetzner.com (от €4/месяц)
- **Vultr**: https://www.vultr.com (от $2.50/месяц)
- **Timeweb**: https://timeweb.com (российский хостинг)

### 2. Облачные платформы (PaaS)
- **Railway**: https://railway.app (бесплатный тариф доступен)
- **Render**: https://render.com (бесплатный тариф доступен)
- **Fly.io**: https://fly.io (бесплатный тариф доступен)
- **Heroku**: https://www.heroku.com (платный)

## Способ 1: Развёртывание на VPS (Linux)

### Шаг 1: Подключение к серверу

```bash
ssh root@ваш_сервер_ip
```

### Шаг 2: Установка Python и зависимостей

```bash
# Обновление системы (Ubuntu/Debian)
apt update && apt upgrade -y

# Установка Python 3.11+ и pip
apt install python3 python3-pip python3-venv git -y

# Создание пользователя для бота (опционально, но рекомендуется)
adduser botuser
su - botuser
```

### Шаг 3: Клонирование репозитория

```bash
cd ~
git clone https://github.com/nonmagicfly/bot_ai_cursor.git
cd bot_ai_cursor
```

### Шаг 4: Настройка виртуального окружения

```bash
# Создание виртуального окружения
python3 -m venv venv

# Активация
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### Шаг 5: Настройка переменных окружения

```bash
# Создание файла .env
nano .env
```

Добавьте в файл:
```
BOT_TOKEN=ваш_токен_бота
DATABASE=./data/gym.db
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

### Шаг 6: Инициализация базы данных

```bash
python3 db_init.py
```

### Шаг 7: Запуск бота как системного сервиса (systemd)

Создайте файл сервиса:

```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Добавьте содержимое:

```ini
[Unit]
Description=Telegram Workout Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/bot_ai_cursor
Environment="PATH=/home/botuser/bot_ai_cursor/venv/bin"
ExecStart=/home/botuser/bot_ai_cursor/venv/bin/python3 bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Важно:** Замените `/home/botuser/bot_ai_cursor` на ваш реальный путь!

Активируйте и запустите сервис:

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable telegram-bot

# Запуск бота
sudo systemctl start telegram-bot

# Проверка статуса
sudo systemctl status telegram-bot

# Просмотр логов
sudo journalctl -u telegram-bot -f
```

### Альтернатива: Запуск через screen/tmux

```bash
# Установка screen
apt install screen -y

# Создание сессии
screen -S bot

# Активация окружения и запуск
source venv/bin/activate
python3 bot.py

# Отключение: Ctrl+A, затем D
# Подключение обратно: screen -r bot
```

---

## Способ 2: Развёртывание на Railway

### Шаг 1: Регистрация и подключение GitHub

1. Перейдите на https://railway.app
2. Войдите через GitHub
3. Нажмите "New Project" → "Deploy from GitHub repo"
4. Выберите репозиторий `bot_ai_cursor`

### Шаг 2: Настройка переменных окружения

1. В проекте Railway откройте вкладку "Variables"
2. Добавьте переменные:
   - `BOT_TOKEN` = ваш токен бота
   - `DATABASE` = `./data/gym.db`

### Шаг 3: Настройка команды запуска

1. Откройте вкладку "Settings"
2. В разделе "Deploy" установите:
   - **Build Command**: `pip install -r requirements.txt && python db_init.py`
   - **Start Command**: `python bot.py`

### Шаг 4: Деплой

Railway автоматически задеплоит проект. Проверьте логи в разделе "Deployments".

---

## Способ 3: Развёртывание на Render

### Шаг 1: Создание Web Service

1. Перейдите на https://render.com
2. Войдите через GitHub
3. Нажмите "New" → "Web Service"
4. Подключите репозиторий `bot_ai_cursor`

### Шаг 2: Настройка

- **Name**: `telegram-workout-bot`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt && python db_init.py`
- **Start Command**: `python bot.py`

### Шаг 3: Переменные окружения

В разделе "Environment" добавьте:
- `BOT_TOKEN` = ваш токен
- `DATABASE` = `./data/gym.db`

### Шаг 4: Деплой

Нажмите "Create Web Service". Render автоматически задеплоит проект.

**Важно для Render:** На бесплатном тарифе сервис "засыпает" после 15 минут неактивности. Для постоянной работы нужен платный тариф или используйте VPS.

---

## Способ 4: Развёртывание на Fly.io

### Шаг 1: Установка Fly CLI

```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Linux/Mac
curl -L https://fly.io/install.sh | sh
```

### Шаг 2: Создание файла fly.toml

Создайте файл `fly.toml` в корне проекта:

```toml
app = "telegram-workout-bot"
primary_region = "fra"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  BOT_TOKEN = "ваш_токен_здесь"
  DATABASE = "./data/gym.db"

[[services]]
  internal_port = 8080
  protocol = "tcp"
```

### Шаг 3: Деплой

```bash
# Логин
fly auth login

# Создание приложения
fly launch

# Деплой
fly deploy
```

---

## Проверка работы бота

После развёртывания проверьте:

1. **Логи**: Убедитесь, что бот запустился без ошибок
2. **Telegram**: Отправьте команду `/start` боту
3. **База данных**: Проверьте, что файл базы данных создался

## Мониторинг и обслуживание

### Просмотр логов (systemd)

```bash
# Последние 100 строк
sudo journalctl -u telegram-bot -n 100

# Следить за логами в реальном времени
sudo journalctl -u telegram-bot -f
```

### Перезапуск бота (systemd)

```bash
sudo systemctl restart telegram-bot
```

### Обновление кода (VPS)

```bash
cd ~/bot_ai_cursor
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegram-bot
```

## Рекомендации

1. **Безопасность**: Не храните токены в коде, используйте переменные окружения
2. **Резервное копирование**: Регулярно делайте бэкап базы данных `data/gym.db`
3. **Мониторинг**: Настройте уведомления об ошибках (можно через логи)
4. **Обновления**: Регулярно обновляйте зависимости: `pip install --upgrade -r requirements.txt`

## Решение проблем

### Бот не запускается

1. Проверьте логи на наличие ошибок
2. Убедитесь, что токен правильный
3. Проверьте, что база данных инициализирована
4. Убедитесь, что все зависимости установлены

### Бот падает с ошибками

1. Проверьте логи: `journalctl -u telegram-bot -n 50`
2. Убедитесь, что есть доступ к интернету
3. Проверьте права доступа к файлам базы данных

### База данных не создаётся

1. Убедитесь, что папка `data/` существует и доступна для записи
2. Запустите `python db_init.py` вручную
3. Проверьте права доступа: `chmod 755 data/`

