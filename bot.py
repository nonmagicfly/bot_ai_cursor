"""
Telegram-бот для записи силовых упражнений
Использует aiogram 3.x для работы с Telegram Bot API
"""
import os
import logging
import time
import asyncio
from functools import wraps
from datetime import datetime, date
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import aiosqlite
from metrics import (
    users_total, users_active_today, operations_total, operations_today,
    programs_total, programs_active, records_total, records_today,
    request_duration, request_errors, update_system_metrics
)

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_PATH = os.getenv('DATABASE', './data/gym.db')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в переменных окружения!")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# FSM состояния
class WorkoutStates(StatesGroup):
    waiting_for_program_name = State()
    waiting_for_program_text = State()
    waiting_for_weight = State()


# Функции для работы с пользователями
async def register_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    """Регистрация или обновление информации о пользователе"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_activity)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, username, first_name, last_name))
            await db.commit()
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя: {e}")


async def log_operation(user_id: int, operation_type: str):
    """Логирование операции пользователя"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT INTO operations (user_id, operation_type)
                VALUES (?, ?)
            ''', (user_id, operation_type))
            await db.commit()
    except Exception as e:
        logger.error(f"Ошибка при логировании операции: {e}")


# Декоратор для отслеживания операций
def track_operation(operation_type: str):
    """Декоратор для отслеживания операций и метрик"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем user_id из аргументов (args и kwargs)
            user_id = None
            
            # Проверяем args
            for arg in args:
                if isinstance(arg, Message):
                    user_id = arg.from_user.id
                    # Регистрируем пользователя
                    await register_user(
                        user_id=arg.from_user.id,
                        username=arg.from_user.username,
                        first_name=arg.from_user.first_name,
                        last_name=arg.from_user.last_name
                    )
                    break
                elif isinstance(arg, CallbackQuery):
                    user_id = arg.from_user.id
                    await register_user(
                        user_id=arg.from_user.id,
                        username=arg.from_user.username,
                        first_name=arg.from_user.first_name,
                        last_name=arg.from_user.last_name
                    )
                    break
            
            # Проверяем kwargs (на случай, если aiogram передает через dependency injection)
            if not user_id:
                for key, value in kwargs.items():
                    if isinstance(value, Message):
                        user_id = value.from_user.id
                        await register_user(
                            user_id=value.from_user.id,
                            username=value.from_user.username,
                            first_name=value.from_user.first_name,
                            last_name=value.from_user.last_name
                        )
                        break
                    elif isinstance(value, CallbackQuery):
                        user_id = value.from_user.id
                        await register_user(
                            user_id=value.from_user.id,
                            username=value.from_user.username,
                            first_name=value.from_user.first_name,
                            last_name=value.from_user.last_name
                        )
                        break
            
            # Логируем операцию
            if user_id:
                await log_operation(user_id, operation_type)
                operations_total.labels(operation_type=operation_type).inc()
            
            # Отслеживаем время выполнения
            start_time = time.time()
            try:
                # Передаем все аргументы как есть (включая возможные dependency injection аргументы)
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                request_duration.labels(handler=operation_type).observe(duration)
                return result
            except Exception as e:
                request_errors.labels(error_type=type(e).__name__).inc()
                raise
        
        # Сохраняем оригинальную сигнатуру функции
        wrapper.__signature__ = func.__signature__ if hasattr(func, '__signature__') else None
        return wrapper
    return decorator


async def update_metrics():
    """Обновление метрик из базы данных"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Пользователи
            cursor = await db.execute('SELECT COUNT(*) FROM users')
            total_users = (await cursor.fetchone())[0]
            users_total.set(total_users)
            
            # Активные пользователи за сегодня
            today = date.today().isoformat()
            cursor = await db.execute('''
                SELECT COUNT(DISTINCT user_id) FROM operations 
                WHERE date(created_at) = ?
            ''', (today,))
            active_today = (await cursor.fetchone())[0]
            users_active_today.set(active_today)
            
            # Программы
            cursor = await db.execute('SELECT COUNT(*) FROM programs')
            total_programs = (await cursor.fetchone())[0]
            programs_total.set(total_programs)
            
            cursor = await db.execute('SELECT COUNT(*) FROM programs WHERE active = 1')
            active_programs = (await cursor.fetchone())[0]
            programs_active.set(active_programs)
            
            # Записи
            cursor = await db.execute('SELECT COUNT(*) FROM records')
            total_records = (await cursor.fetchone())[0]
            records_total.set(total_records)
            
            cursor = await db.execute('SELECT COUNT(*) FROM records WHERE date = ?', (today,))
            records_today_count = (await cursor.fetchone())[0]
            records_today.set(records_today_count)
            
            # Операции за сегодня
            cursor = await db.execute('''
                SELECT operation_type, COUNT(*) 
                FROM operations 
                WHERE date(created_at) = ?
                GROUP BY operation_type
            ''', (today,))
            async for row in cursor:
                op_type, count = row
                operations_today.labels(operation_type=op_type).set(count)
            
            # Системные метрики
            update_system_metrics()
            
    except Exception as e:
        logger.error(f"Ошибка при обновлении метрик: {e}")


# Функции для работы с БД
async def archive_all_programs():
    """Архивировать все программы (active=0)"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('UPDATE programs SET active = 0')
            await db.commit()
    except Exception as e:
        logger.error(f"Ошибка при архивировании программ: {e}")
        raise


async def delete_all_programs():
    """Удалить все программы и связанные данные"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Удаляем записи тренировок
            await db.execute('DELETE FROM records')
            # Удаляем упражнения
            await db.execute('DELETE FROM exercises')
            # Удаляем программы
            await db.execute('DELETE FROM programs')
            await db.commit()
    except Exception as e:
        logger.error(f"Ошибка при удалении программ: {e}")
        raise


async def create_program(name: str) -> int:
    """Создать новую программу и вернуть её ID"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute(
                'INSERT INTO programs (name, active) VALUES (?, 1)',
                (name,)
            )
            await db.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Ошибка при создании программы: {e}")
        raise


async def add_exercise(program_id: int, day: str, exercise: str, sets: int, position: int):
    """Добавить упражнение в программу"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            'INSERT INTO exercises (program_id, day, exercise, sets, position) VALUES (?, ?, ?, ?, ?)',
            (program_id, day, exercise, sets, position)
        )
        await db.commit()


async def get_active_programs():
    """Получить список активных программ"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('SELECT id, name FROM programs WHERE active = 1 ORDER BY created_at ASC') as cursor:
            return await cursor.fetchall()


async def get_all_programs():
    """Получить список всех программ (активных и архивных)"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('SELECT id, name, active, created_at FROM programs ORDER BY created_at ASC') as cursor:
            return await cursor.fetchall()


async def get_program_exercises(program_id: int):
    """Получить упражнения программы, отсортированные по position"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            'SELECT id, day, exercise, sets, position FROM exercises WHERE program_id = ? ORDER BY position',
            (program_id,)
        ) as cursor:
            return await cursor.fetchall()


async def save_record(program_id: int, exercise_id: int, set_number: int, weight: float):
    """Сохранить запись о выполнении подхода"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                'INSERT INTO records (program_id, exercise_id, set_number, weight, date) VALUES (?, ?, ?, ?, date("now"))',
                (program_id, exercise_id, set_number, weight)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Ошибка при сохранении записи в БД: {e}")
        raise


async def get_records_day():
    """Получить записи за сегодня"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT r.date, p.name, e.exercise, r.set_number, r.weight
            FROM records r
            JOIN programs p ON r.program_id = p.id
            JOIN exercises e ON r.exercise_id = e.id
            WHERE r.date = date('now')
            ORDER BY r.created_at
        ''') as cursor:
            return await cursor.fetchall()


async def get_records_week():
    """Получить записи за неделю"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT r.date, p.name, e.exercise, r.set_number, r.weight
            FROM records r
            JOIN programs p ON r.program_id = p.id
            JOIN exercises e ON r.exercise_id = e.id
            WHERE r.date >= date('now', '-7 days')
            ORDER BY r.date, r.created_at
        ''') as cursor:
            return await cursor.fetchall()


async def get_records_all():
    """Получить все записи"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT r.date, p.name, e.exercise, r.set_number, r.weight
            FROM records r
            JOIN programs p ON r.program_id = p.id
            JOIN exercises e ON r.exercise_id = e.id
            ORDER BY r.date DESC, r.created_at
        ''') as cursor:
            return await cursor.fetchall()


async def init_db():
    """Проверка и инициализация БД"""
    # Проверяем существование файла БД
    if not os.path.exists(DATABASE_PATH):
        logger.warning(f"База данных не найдена: {DATABASE_PATH}")
        logger.info("Запустите db_init.py для создания базы данных")
    else:
        logger.info(f"База данных найдена: {DATABASE_PATH}")


# Обработчики команд
@dp.message(Command("start"))
@track_operation("start")
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = """
🏋️ Добро пожаловать в бот для записи силовых упражнений!

Доступные команды:
/start - Начать работу
/newprogram - Создать новую программу тренировок
/programs - Список всех программ
/startworkout - Начать тренировку
/report - Просмотреть отчёты
/deleteall - Удалить все программы

Для создания программы:
1. Введите название программы
2. Введите упражнения в формате: упражнение\\подходы

Пример:
Приседания\\3
Жим лёжа\\3
Тяга\\3
    """
    await message.answer(welcome_text)


@dp.message(Command("newprogram"))
@track_operation("newprogram")
async def cmd_newprogram(message: Message, state: FSMContext):
    """Обработчик команды /newprogram"""
    await message.answer(
        "📝 Введите название программы:"
    )
    await state.set_state(WorkoutStates.waiting_for_program_name)


@dp.message(WorkoutStates.waiting_for_program_name)
async def process_program_name(message: Message, state: FSMContext):
    """Обработка названия программы"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введите название программы.")
        return
    
    program_name = message.text.strip()
    
    if not program_name:
        await message.answer("❌ Название программы не может быть пустым. Попробуйте снова.")
        return
    
    # Сохраняем название программы в состоянии
    await state.update_data(program_name=program_name)
    
    # Запрашиваем текст программы
    await message.answer(
        f"📝 Название программы: {program_name}\n\n"
        f"Теперь введите упражнения в формате:\n"
        f"упражнение\\подходы\n\n"
        f"Пример:\n"
        f"Приседания\\3\n"
        f"Жим лёжа\\3\n"
        f"Тяга\\3"
    )
    await state.set_state(WorkoutStates.waiting_for_program_text)


@dp.message(WorkoutStates.waiting_for_program_text)
async def process_program_text(message: Message, state: FSMContext):
    """Обработка текста программы"""
    if not message.text:
        await message.answer("❌ Пожалуйста, отправьте текст программы.")
        return
    
    # Получаем название программы из состояния
    data = await state.get_data()
    program_name = data.get('program_name')
    
    if not program_name:
        await message.answer("❌ Ошибка: название программы не найдено. Начните заново командой /newprogram")
        await state.clear()
        return
    
    program_text = message.text.strip()
    
    try:
        # Парсинг строк программы
        lines = [line.strip() for line in program_text.split('\n') if line.strip()]
        
        if not lines:
            await message.answer("❌ Программа пуста. Попробуйте снова.")
            await state.clear()
            return
        
        # Создаём новую программу (старые программы остаются активными)
        program_id = await create_program(program_name)
        
        # Парсим и добавляем упражнения (формат: упражнение\подходы)
        position = 0
        for line in lines:
            parts = line.split('\\')
            if len(parts) != 2:
                continue
            
            exercise = parts[0].strip()
            try:
                sets = int(parts[1].strip())
            except ValueError:
                continue
            
            # Используем пустое значение для дня, так как формат изменился
            day = "Общий"
            await add_exercise(program_id, day, exercise, sets, position)
            position += 1
        
        if position == 0:
            await message.answer(
                "❌ Не удалось распарсить упражнения. Проверьте формат:\n"
                "упражнение\\подходы"
            )
            await state.clear()
            return
        
        await message.answer(
            f"✅ Программа '{program_name}' создана!\n"
            f"Добавлено упражнений: {position}"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при создании программы: {e}")
        await message.answer("❌ Ошибка при создании программы. Попробуйте снова.")
    
    await state.clear()


@dp.message(Command("startworkout"))
@track_operation("startworkout")
async def cmd_startworkout(message: Message, state: FSMContext):
    """Обработчик команды /startworkout - выбор активной программы для тренировки"""
    # Очищаем предыдущее состояние, если было
    await state.clear()
    
    # Получаем только активные программы
    programs = await get_active_programs()
    
    if not programs:
        await message.answer(
            "❌ Нет активных программ.\n\n"
            "Создайте программу командой /newprogram"
        )
        return
    
    # Создаём инлайн-клавиатуру с активными программами
    buttons = []
    for program_id, program_name in programs:
        buttons.append([InlineKeyboardButton(
            text=program_name,
            callback_data=f"select_program_{program_id}"
        )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    programs_list = "\n".join([f"• {p[1]}" for p in programs])
    await message.answer(
        f"🏋️ Выберите активную программу для тренировки:\n\n{programs_list}",
        reply_markup=keyboard
    )


@dp.callback_query(F.data.startswith("select_program_"))
async def process_program_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора активной программы через инлайн-кнопку"""
    await callback.answer()
    
    # Регистрируем пользователя и логируем операцию
    user_id = callback.from_user.id
    await register_user(
        user_id=user_id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name
    )
    await log_operation(user_id, "select_program")
    operations_total.labels(operation_type="select_program").inc()
    
    # Извлекаем ID программы из callback_data
    try:
        program_id = int(callback.data.split("_")[2])
    except (ValueError, IndexError):
        await callback.message.answer("❌ Ошибка при выборе программы. Попробуйте снова.")
        return
    
    # Дополнительная проверка, что программа действительно активна
    active_programs = await get_active_programs()
    active_ids = [p[0] for p in active_programs]
    
    if program_id not in active_ids:
        await callback.message.answer(
            "❌ Эта программа больше не активна.\n"
            "Используйте команду /startworkout для выбора активной программы."
        )
        return
    
    # Находим название программы
    program_name = next((p[1] for p in active_programs if p[0] == program_id), None)
    
    if not program_name:
        await callback.message.answer("❌ Программа не найдена.")
        return
    
    # Получаем упражнения программы
    exercises = await get_program_exercises(program_id)
    
    if not exercises:
        await callback.message.answer("❌ В программе нет упражнений.")
        return
    
    # Сохраняем данные для процесса тренировки
    await state.update_data(
        program_id=program_id,
        program_name=program_name,
        exercises=exercises,
        current_exercise_index=0,
        current_set=1
    )
    
    # Удаляем инлайн-клавиатуру (если возможно)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        logger.warning(f"Не удалось удалить клавиатуру: {e}")
        # Продолжаем работу даже если не удалось удалить клавиатуру
    
    # Начинаем с первого упражнения
    await process_next_exercise(callback.message, state)


async def process_next_exercise(message: Message, state: FSMContext):
    """Обработка следующего упражнения"""
    data = await state.get_data()
    
    # Проверяем наличие необходимых данных
    if 'exercises' not in data or 'current_exercise_index' not in data:
        await message.answer("❌ Ошибка состояния. Начните тренировку заново командой /startworkout")
        await state.clear()
        return
    
    exercises = data['exercises']
    current_index = data['current_exercise_index']
    
    if current_index >= len(exercises):
        # Все упражнения выполнены
        await message.answer(
            "✅ Тренировка завершена!",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()
        return
    
    exercise = exercises[current_index]
    exercise_id, day, exercise_name, sets, position = exercise
    
    await state.update_data(
        current_exercise_id=exercise_id,
        current_exercise_name=exercise_name,
        current_day=day,
        total_sets=sets,
        current_set=1
    )
    
    # Формируем сообщение с учётом дня
    if day and day != "Общий":
        message_text = (
            f"📅 День: {day}\n"
            f"🏋️ Упражнение: {exercise_name}\n"
            f"📊 Подходов: {sets}\n\n"
            f"Введите вес для подхода 1 (в кг):"
        )
    else:
        message_text = (
            f"🏋️ Упражнение: {exercise_name}\n"
            f"📊 Подходов: {sets}\n\n"
            f"Введите вес для подхода 1 (в кг):"
        )
    
    await message.answer(message_text, reply_markup=ReplyKeyboardRemove())
    
    await state.set_state(WorkoutStates.waiting_for_weight)


@dp.message(WorkoutStates.waiting_for_weight)
async def process_weight(message: Message, state: FSMContext):
    """Обработка ввода веса"""
    # Получаем данные о текущем подходе
    data = await state.get_data()
    
    # Проверяем наличие необходимых данных
    if 'current_set' not in data or 'total_sets' not in data:
        await message.answer("❌ Ошибка состояния. Начните тренировку заново командой /startworkout")
        await state.clear()
        return
    
    current_set = data['current_set']
    total_sets = data['total_sets']
    exercise_name = data.get('current_exercise_name', 'упражнение')
    day = data.get('current_day', '')
    
    # Проверяем наличие текста
    if not message.text:
        if day and day != "Общий":
            error_text = (
                f"❌ Пожалуйста, введите вес числом:\n\n"
                f"📅 День: {day}\n"
                f"🏋️ Упражнение: {exercise_name}\n"
                f"📊 Подход {current_set}/{total_sets}"
            )
        else:
            error_text = (
                f"❌ Пожалуйста, введите вес числом:\n\n"
                f"🏋️ Упражнение: {exercise_name}\n"
                f"📊 Подход {current_set}/{total_sets}"
            )
        await message.answer(error_text)
        return
    
    # Проверяем формат введённого веса
    try:
        weight = float(message.text.replace(',', '.'))
    except (ValueError, AttributeError, TypeError):
        # При ошибке формата продолжаем запрашивать вес для того же подхода
        if day and day != "Общий":
            error_text = (
                f"❌ Неверный формат. Введите число (например: 80 или 80.5):\n\n"
                f"📅 День: {day}\n"
                f"🏋️ Упражнение: {exercise_name}\n"
                f"📊 Подход {current_set}/{total_sets}"
            )
        else:
            error_text = (
                f"❌ Неверный формат. Введите число (например: 80 или 80.5):\n\n"
                f"🏋️ Упражнение: {exercise_name}\n"
                f"📊 Подход {current_set}/{total_sets}"
            )
        await message.answer(error_text)
        return  # Возвращаемся, но состояние остаётся waiting_for_weight, поэтому запрос продолжится
    
    # Если формат правильный, сохраняем запись
    if 'program_id' not in data or 'current_exercise_id' not in data:
        await message.answer("❌ Ошибка состояния. Начните тренировку заново командой /startworkout")
        await state.clear()
        return
    
    program_id = data['program_id']
    exercise_id = data['current_exercise_id']
    
    # Сохраняем запись
    try:
        await save_record(program_id, exercise_id, current_set, weight)
        # Логируем операцию сохранения записи
        await log_operation(message.from_user.id, "save_record")
    except Exception as e:
        logger.error(f"Ошибка при сохранении записи: {e}")
        await message.answer("❌ Ошибка при сохранении записи. Попробуйте снова.")
        return
    
    await message.answer(
        f"✅ {exercise_name}\n"
        f"Подход {current_set}/{total_sets}: {weight} кг записан"
    )
    
    # Переходим к следующему подходу или упражнению
    if current_set < total_sets:
        await state.update_data(current_set=current_set + 1)
        await message.answer(
            f"🏋️ {exercise_name}\n"
            f"Введите вес для подхода {current_set + 1}/{total_sets} (в кг):"
        )
    else:
        # Переходим к следующему упражнению
        await state.update_data(current_exercise_index=data['current_exercise_index'] + 1)
        await process_next_exercise(message, state)


@dp.message(Command("programs"))
@track_operation("programs")
async def cmd_programs(message: Message):
    """Обработчик команды /programs - показать список всех программ"""
    programs = await get_all_programs()
    
    if not programs:
        await message.answer("📝 У вас пока нет программ. Создайте программу командой /newprogram")
        return
    
    # Формируем список программ
    programs_text = "📋 Список программ:\n\n"
    
    for program in programs:
        program_id, name, active, created_at = program
        status = "✅ Активна" if active == 1 else "📦 Архив"
        programs_text += f"{status} - {name}\n"
        programs_text += f"   ID: {program_id} | Создана: {created_at}\n\n"
    
    # Подсчитываем статистику
    active_count = sum(1 for p in programs if p[2] == 1)
    archived_count = len(programs) - active_count
    
    programs_text += f"Всего программ: {len(programs)}\n"
    programs_text += f"Активных: {active_count}\n"
    programs_text += f"В архиве: {archived_count}"
    
    await message.answer(programs_text)


@dp.message(Command("deleteall"))
@track_operation("deleteall")
async def cmd_deleteall(message: Message, state: FSMContext):
    """Обработчик команды /deleteall - удаление всех программ"""
    # Создаём инлайн-клавиатуру с подтверждением
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить все", callback_data="confirm_delete_all")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete_all")]
    ])
    
    await message.answer(
        "⚠️ ВНИМАНИЕ!\n\n"
        "Вы собираетесь удалить ВСЕ программы и все записи тренировок.\n"
        "Это действие нельзя отменить!\n\n"
        "Продолжить?",
        reply_markup=keyboard
    )


@dp.callback_query(F.data == "confirm_delete_all")
async def confirm_delete_all(callback: CallbackQuery):
    """Подтверждение удаления всех программ"""
    await callback.answer()
    
    try:
        await delete_all_programs()
        await callback.message.edit_text(
            "✅ Все программы и записи тренировок удалены.",
            reply_markup=None
        )
    except Exception as e:
        logger.error(f"Ошибка при удалении программ: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при удалении программ. Попробуйте снова.",
            reply_markup=None
        )


@dp.callback_query(F.data == "cancel_delete_all")
async def cancel_delete_all(callback: CallbackQuery):
    """Отмена удаления всех программ"""
    await callback.answer("Отменено")
    await callback.message.edit_text(
        "❌ Удаление отменено.",
        reply_markup=None
    )


@dp.message(Command("report"))
@track_operation("report")
async def cmd_report(message: Message):
    """Обработчик команды /report"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="За день")],
            [KeyboardButton(text="За неделю")],
            [KeyboardButton(text="За всё время")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer("Выберите период для отчёта:", reply_markup=keyboard)


@dp.message(lambda m: m.text in ["За день", "За неделю", "За всё время"])
async def process_report_selection(message: Message):
    """Обработка выбора периода отчёта"""
    if not message.text:
        return
    
    period = message.text
    
    if period == "За день":
        records = await get_records_day()
        period_text = "за сегодня"
    elif period == "За неделю":
        records = await get_records_week()
        period_text = "за неделю"
    else:
        records = await get_records_all()
        period_text = "за всё время"
    
    if not records:
        await message.answer(
            f"📊 Отчёт {period_text}:\n\nНет записей.",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    # Группируем записи по дате, программе и упражнению
    grouped_records = {}
    for record in records:
        date_str, program_name, exercise, set_number, weight = record
        key = (date_str, program_name, exercise)
        
        if key not in grouped_records:
            grouped_records[key] = []
        
        grouped_records[key].append(weight)
    
    # Формируем отчёт
    report_lines = [f"📊 Отчёт {period_text}:\n"]
    
    for (date_str, program_name, exercise), weights in grouped_records.items():
        # Сортируем веса по порядку (если нужно сохранить порядок подходов)
        # weights уже в порядке создания благодаря ORDER BY в SQL
        weights_str = ", ".join([f"{w} кг" for w in weights])
        sets_count = len(weights)
        report_lines.append(
            f"{date_str} | {program_name} | {exercise} ({sets_count} подхода) | {weights_str}"
        )
    
    report_text = "\n".join(report_lines)
    
    # Разбиваем на части, если сообщение слишком длинное
    max_length = 4000
    if len(report_text) > max_length:
        chunks = [report_text[i:i+max_length] for i in range(0, len(report_text), max_length)]
        for chunk in chunks:
            await message.answer(chunk, reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(report_text, reply_markup=ReplyKeyboardRemove())


@dp.message(F.text & ~F.text.startswith('/'))
async def handle_unknown_command(message: Message, state: FSMContext):
    """Обработчик неизвестных команд - показывает меню"""
    # Проверяем, не находимся ли мы в FSM состоянии
    current_state = await state.get_state()
    
    # Если находимся в состоянии ожидания ввода (вес, название программы, текст программы),
    # не показываем меню, а пропускаем обработку (другие обработчики обработают)
    if current_state:
        state_name = str(current_state)
        if any(state in state_name for state in [
            'waiting_for_program_name',
            'waiting_for_program_text',
            'waiting_for_weight'
        ]):
            return  # Пропускаем, пусть обрабатывают специализированные обработчики
    
    # Если это не специальные тексты (выбор периода отчёта), показываем меню
    if message.text not in ["За день", "За неделю", "За всё время"]:
        welcome_text = """
🏋️ Добро пожаловать в бот для записи силовых упражнений!

Доступные команды:
/start - Начать работу
/newprogram - Создать новую программу тренировок
/programs - Список всех программ
/startworkout - Начать тренировку
/report - Просмотреть отчёты
/deleteall - Удалить все программы

Для создания программы:
1. Введите название программы
2. Введите упражнения в формате: упражнение\\подходы

Пример:
Приседания\\3
Жим лёжа\\3
Тяга\\3
        """
        await message.answer(welcome_text)


async def periodic_metrics_update():
    """Периодическое обновление метрик"""
    while True:
        try:
            await asyncio.sleep(30)  # Обновляем каждые 30 секунд
            await update_metrics()
        except Exception as e:
            logger.error(f"Ошибка при обновлении метрик: {e}")


async def main():
    """Основная функция запуска бота"""
    try:
        # Инициализация БД
        await init_db()
        
        # Запуск HTTP сервера для метрик
        from metrics_server import run_metrics_server
        metrics_port = int(os.getenv('METRICS_PORT', '8000'))
        metrics_runner = await run_metrics_server(metrics_port)
        logger.info(f"HTTP сервер метрик запущен на порту {metrics_port}")
        
        # Запуск периодического обновления метрик
        metrics_task = asyncio.create_task(periodic_metrics_update())
        
        # Первоначальное обновление метрик
        await update_metrics()
        
        logger.info("Бот запущен...")
        
        # Запуск polling
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        raise
    finally:
        # Остановка сервера метрик
        if 'metrics_runner' in locals():
            await metrics_runner.cleanup()
        if 'metrics_task' in locals():
            metrics_task.cancel()


if __name__ == '__main__':
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Завершение работы...")
