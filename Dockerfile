# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем curl для health check
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .

# Создаём папку для базы данных
RUN mkdir -p data

# Копируем и делаем исполняемым скрипт запуска
COPY start.sh .
RUN chmod +x start.sh

# Указываем команду запуска (скрипт инициализирует БД и запускает бота)
CMD ["./start.sh"]

