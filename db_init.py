"""
Скрипт для инициализации базы данных
Создаёт структуру БД для хранения программ тренировок и записей
"""
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Путь к базе данных
DATABASE_PATH = os.getenv('DATABASE', './data/gym.db')


def create_data_directory():
    """Создать папку data/ если её нет"""
    db_path = Path(DATABASE_PATH)
    data_dir = db_path.parent
    
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Создана папка: {data_dir}")
    else:
        print(f"[INFO] Папка уже существует: {data_dir}")


def init_database():
    """Инициализация базы данных и создание всех таблиц"""
    print(f"Инициализация базы данных: {DATABASE_PATH}")
    
    # Создать папку data/ если её нет
    create_data_directory()
    
    # Подключение к базе данных
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Создание таблицы programs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS programs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active INTEGER DEFAULT 0
            )
        ''')
        print("[OK] Таблица 'programs' создана")
        
        # Создание таблицы exercises
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id INTEGER NOT NULL,
                day TEXT NOT NULL,
                exercise TEXT NOT NULL,
                sets INTEGER NOT NULL,
                position INTEGER NOT NULL,
                FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE
            )
        ''')
        print("[OK] Таблица 'exercises' создана")
        
        # Создание таблицы records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                date DATE DEFAULT (date('now')),
                set_number INTEGER NOT NULL,
                weight REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE,
                FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
            )
        ''')
        print("[OK] Таблица 'records' создана")
        
        # Создание индексов для оптимизации запросов
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_exercises_program_id 
            ON exercises(program_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_records_program_id 
            ON records(program_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_records_exercise_id 
            ON records(exercise_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_records_date 
            ON records(date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_programs_active 
            ON programs(active)
        ''')
        
        print("[OK] Индексы созданы")
        
        # Сохранение изменений
        conn.commit()
        
        # Проверка существующих данных
        cursor.execute('SELECT COUNT(*) FROM programs')
        programs_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM exercises')
        exercises_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM records')
        records_count = cursor.fetchone()[0]
        
        print("\n" + "=" * 50)
        print("[OK] База данных успешно инициализирована!")
        print(f"   Программ в базе: {programs_count}")
        print(f"   Упражнений в базе: {exercises_count}")
        print(f"   Записей в базе: {records_count}")
        print("=" * 50)
        
    except sqlite3.Error as e:
        print(f"[ERROR] Ошибка при создании базы данных: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    """Основная функция"""
    print("=" * 50)
    print("Инициализация базы данных для бота тренировок")
    print("=" * 50)
    print()
    
    try:
        init_database()
        print("\n[OK] Готово! Теперь можно запускать бота командой: python bot.py")
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
