import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import uuid
import re
from dotenv import load_dotenv
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')

# Состояния для ConversationHandler
CHOOSING, GIFT = range(2)

# Загрузка переменных окружения
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')


# Создание подключения
async def get_db_connection():
    conn = await asyncpg.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )
    return conn


def create_database():
    """Создание базы данных и таблиц для хранения данных пользователей и подарков."""
    conn = sqlite3.connect('gift_bot.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        birthday TEXT NOT NULL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS gifts (
                        gift_id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        gift_name TEXT,
                        invite_code TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(user_id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS users_invite_links (
                        link_id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        invite_code TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(user_id))''')

    conn.commit()
    conn.close()

create_database()

def get_db_connection():
    """Получение соединения с базой данных SQLite."""
    conn = sqlite3.connect('gift_bot.db')
    conn.row_factory = sqlite3.Row  # Для получения результатов как словаря
    return conn

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start для приветствия и вывода доступных команд."""
    if context.args:
        invite_code = context.args[0]

        if invite_code in get_invite_codes():
            context.user_data['invite_code'] = invite_code
            await update.message.reply_text("Введите подарок, который хотите предложить:")
            return GIFT

    # Основное меню
    welcome_text = (
        "Привет! Я бот для организации дня рождения.\n"
        "Доступные команды:\n"
        "/registration_for_the_birthday - Зарегистрировать день рождения.\n"
        "/create_the_link - Создать ссылку для рассылки гостям.\n"
        "/guest_profile - Просмотр своего профиля (для гостей)."
    )

    keyboard = [
        ["/registration_for_the_birthday", "/create_the_link"],
        ["/guest_profile"],
        ["/start"]
    ]

    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(welcome_text, reply_markup=markup)

async def registration_for_the_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запрос имени и дня рождения для регистрации."""
    await update.message.reply_text(
        'Введите ваше имя и дату рождения в формате: Имя ДД.ММ.ГГ (например: Иван 09.09.1999):')
    return CHOOSING

async def save_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сохранение имени и дня рождения пользователя в базе данных."""
    user_id = update.effective_user.id
    input_text = update.message.text
    pattern = r"^([A-Za-zА-Яа-я]+)\ (\d{2})\.(\d{2})\.(\d{4})$"
    match = re.match(pattern, input_text)

    if match:
        name = match.group(1)
        birthday = f"{match.group(2)}.{match.group(3)}.{match.group(4)}"

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.execute('UPDATE users SET name = ?, birthday = ? WHERE user_id = ?',
                           (name, birthday, user_id))
            conn.commit()
            conn.close()
            await update.message.reply_text(f"Ваши данные обновлены: {name}, {birthday}.")
        else:
            conn.execute('INSERT INTO users (user_id, name, birthday) VALUES (?, ?, ?)',
                         (user_id, name, birthday))
            conn.commit()
            conn.close()
            await update.message.reply_text(
                f"Ваши данные зарегистрированы: {name}, {birthday}. Теперь используйте команду /create_the_link для создания ссылки.")

        return ConversationHandler.END
    else:
        await update.message.reply_text("Неверный формат. Попробуйте еще раз, например: Иван 09.09.1999")
        return CHOOSING

async def create_the_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создание уникальной ссылки для именинника."""
    user_id = update.effective_user.id

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        await update.message.reply_text(
            "Вы еще не зарегистрировали свой день рождения. Используйте команду /registration_for_the_birthday.")
        return

    invite_code = str(uuid.uuid4().hex[:8])
    conn.execute('INSERT INTO users_invite_links (user_id, invite_code) VALUES (?, ?)',
                 (user_id, invite_code))
    conn.commit()
    conn.close()

    invite_link = f"https://t.me/almizi_and_dini_bot?start={invite_code}"
    await update.message.reply_text(f"Вот ваша ссылка для рассылки гостям:\n{invite_link}")

def get_invite_codes():
    """Получение всех кодов приглашений."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT invite_code FROM users_invite_links')
    codes = cursor.fetchall()
    conn.close()
    return [code['invite_code'] for code in codes]

async def add_gift(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало ввода подарка от гостей."""
    if len(update.message.text.split()) > 1:
        invite_code = update.message.text.split()[1]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users_invite_links WHERE invite_code = ?', (invite_code,))
        if cursor.fetchone():
            context.user_data['invite_code'] = invite_code
            await update.message.reply_text("Введите подарок, который хотите предложить:")
            conn.close()
            return GIFT
        else:
            await update.message.reply_text("Неверная ссылка.")
            conn.close()
            return ConversationHandler.END
    await update.message.reply_text("Сначала получите ссылку от именинника для предложения подарков.")
    return ConversationHandler.END

async def save_gift(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сохранение предложенного подарка в базе данных."""
    user_id = update.effective_user.id
    gift = update.message.text
    invite_code = context.user_data.get('invite_code')

    if not invite_code:
        await update.message.reply_text("Вы должны указать ссылку для добавления подарка.")
        return ConversationHandler.END

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM gifts WHERE user_id = ? AND gift_name = ? AND invite_code = ?',
                   (user_id, gift, invite_code))
    existing_gift = cursor.fetchone()

    if existing_gift:
        await update.message.reply_text(f"Вы уже предложили подарок '{gift}'.")
        conn.close()
        return ConversationHandler.END

    conn.execute('INSERT INTO gifts (user_id, gift_name, invite_code) VALUES (?, ?, ?)',
                 (user_id, gift, invite_code))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Подарок '{gift}' успешно добавлен в список!")
    return ConversationHandler.END

async def guest_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отображение предложенных подарков для гостя."""
    user_id = update.effective_user.id

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT gift_name FROM gifts WHERE user_id = ?', (user_id,))
    gifts = cursor.fetchall()
    conn.close()

    if gifts:
        gift_list = "\n".join([gift['gift_name'] for gift in gifts])
        await update.message.reply_text(f"Ваши предложенные подарки:\n{gift_list}")
    else:
        await update.message.reply_text("Вы еще не предложили подарков.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отмена текущего действия."""
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("registration_for_the_birthday", registration_for_the_birthday)],
    states={
        CHOOSING: [MessageHandler(filters.TEXT, save_birthday)],
        GIFT: [MessageHandler(filters.TEXT, save_gift)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

def main():
    """Основная функция для запуска бота."""
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conversation_handler)
    app.add_handler(CommandHandler("create_the_link", create_the_link))
    app.add_handler(CommandHandler("guest_profile", guest_profile))

    app.run_polling()

if __name__ == "__main__":
    main()
