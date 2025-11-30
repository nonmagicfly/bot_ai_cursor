"""
Модуль для Prometheus метрик
Отслеживает состояние бота, пользователей и операции
"""
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Предупреждение: psutil не установлен. Системные метрики будут недоступны.")
import os

# Метрики пользователей
users_total = Gauge('bot_users_total', 'Общее количество зарегистрированных пользователей')
users_active_today = Gauge('bot_users_active_today', 'Количество активных пользователей за сегодня')

# Метрики операций
operations_total = Counter('bot_operations_total', 'Общее количество операций', ['operation_type'])
operations_today = Gauge('bot_operations_today', 'Количество операций за сегодня', ['operation_type'])

# Метрики базы данных
programs_total = Gauge('bot_programs_total', 'Общее количество программ')
programs_active = Gauge('bot_programs_active', 'Количество активных программ')
records_total = Gauge('bot_records_total', 'Общее количество записей тренировок')
records_today = Gauge('bot_records_today', 'Количество записей за сегодня')

# Метрики производительности
request_duration = Histogram('bot_request_duration_seconds', 'Длительность обработки запросов', ['handler'])
request_errors = Counter('bot_request_errors_total', 'Количество ошибок при обработке запросов', ['error_type'])

# Метрики системы
bot_health = Gauge('bot_health', 'Состояние бота (1 = работает, 0 = не работает)')
bot_uptime = Gauge('bot_uptime_seconds', 'Время работы бота в секундах')
system_cpu_percent = Gauge('bot_system_cpu_percent', 'Загрузка CPU в процентах')
system_memory_percent = Gauge('bot_system_memory_percent', 'Использование памяти в процентах')
system_memory_bytes = Gauge('bot_system_memory_bytes', 'Использование памяти в байтах')

# Время запуска бота
start_time = time.time()

def update_system_metrics():
    """Обновление системных метрик"""
    try:
        if PSUTIL_AVAILABLE:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            system_cpu_percent.set(cpu_percent)
            
            # Memory
            memory = psutil.virtual_memory()
            system_memory_percent.set(memory.percent)
            system_memory_bytes.set(memory.used)
        else:
            # Базовые метрики без psutil
            system_cpu_percent.set(0)
            system_memory_percent.set(0)
            system_memory_bytes.set(0)
        
        # Uptime
        uptime = time.time() - start_time
        bot_uptime.set(uptime)
        
        # Health check
        bot_health.set(1)
    except Exception as e:
        bot_health.set(0)
        print(f"Ошибка обновления системных метрик: {e}")

def get_metrics():
    """Возвращает метрики в формате Prometheus"""
    update_system_metrics()
    return generate_latest()

