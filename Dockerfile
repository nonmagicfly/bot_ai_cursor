# Используем официальный Python образ
FROM python:3.11-slim

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

