import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
from sqlalchemy.orm import Session
from database import TelegramUserDB, get_db
from models import TelegramUser
import os
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.getenv("TG_BOT_TOKEN")

# Список разрешенных команд (доступны всем)
PUBLIC_COMMANDS = ['/start', '/help', '/register']


# ========== ПРОВЕРКА ДОСТУПА ==========
async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, есть ли пользователь в белом списке"""
    user = update.effective_user
    db: Session = next(get_db())

    # Администратор (можно задать конкретный ID)
    if user.id == int(os.getenv("ADMIN_TG_ID", 0)):
        return True

    # Проверяем в БД
    allowed = TelegramUserDB.user_exists(db, user.id)
    db.close()

    if not allowed:
        await update.message.reply_text(
            "❌ У вас нет доступа к этому боту.\n"
            "Обратитесь к администратору для добавления в белый список."
        )
    return allowed


# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"Это бот для уведомлений о сертификатах.\n"
        f"Ваш Telegram ID: `{user.id}`\n\n"
        f"Доступные команды:\n"
        f"/help - помощь\n"
        f"/register - зарегистрироваться в системе\n"
        f"/status - проверить статус\n\n"
        f"*Для администраторов:*\n"
        f"/add_user @username - добавить пользователя\n"
        f"/remove_user @username - удалить пользователя\n"
        f"/list_users - список всех пользователей",
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📚 *Помощь по боту*\n\n"
        "Этот бот будет присылать вам уведомления о:\n"
        "• Сертификатах, срок которых подходит к концу (за 15 дней)\n"
        "• Просроченных сертификатах\n"
        "• Важных событиях в системе\n\n"
        "Уведомления приходят раз в день.",
        parse_mode='Markdown'
    )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Саморегистрация пользователя (только если админ одобрит)"""
    user = update.effective_user
    db: Session = next(get_db())

    if TelegramUserDB.user_exists(db, user.id):
        await update.message.reply_text("✅ Вы уже зарегистрированы в системе!")
        db.close()
        return

    # Отправляем запрос админу (в реальности можно добавить в очередь)
    await update.message.reply_text(
        "📝 Заявка на регистрацию отправлена администратору.\n"
        "Ожидайте подтверждения."
    )

    # Здесь можно уведомить админа через другого бота или лог
    logger.info(f"User @{user.username} (ID: {user.id}) requested registration")
    db.close()


# ========== АДМИН КОМАНДЫ (только для админа) ==========
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить пользователя в белый список (только для админа)"""
    user = update.effective_user

    # Проверяем, админ ли
    if user.id != int(os.getenv("ADMIN_TG_ID", 0)):
        return

    if not context.args:
        await update.message.reply_text("Использование: /add_user @username")
        return

    username = context.args[0].lstrip('@')

    # Здесь нужно получить telegram_id по username
    # В реальности придется либо заставить пользователя написать боту,
    # либо использовать другой механизм

    await update.message.reply_text(
        f"⚠️ Для добавления пользователя @{username} нужно, "
        f"чтобы он сначала написал боту команду /start.\n"
        f"После этого можно будет добавить его по ID."
    )


async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить пользователя из белого списка"""
    user = update.effective_user

    if user.id != int(os.getenv("ADMIN_TG_ID", 0)):
        return

    if not context.args:
        await update.message.reply_text("Использование: /remove_user @username")
        return

    username = context.args[0].lstrip('@')
    db: Session = next(get_db())

    if TelegramUserDB.remove_user(db, username):
        await update.message.reply_text(f"✅ Пользователь @{username} удален из белого списка")
    else:
        await update.message.reply_text(f"❌ Пользователь @{username} не найден")

    db.close()


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать всех пользователей"""
    user = update.effective_user

    if user.id != int(os.getenv("ADMIN_TG_ID", 0)):
        return

    db: Session = next(get_db())
    users = TelegramUserDB.get_all_active_users(db)

    if not users:
        await update.message.reply_text("📭 Нет зарегистрированных пользователей")
        db.close()
        return

    text = "📋 *Список пользователей:*\n\n"
    for u in users:
        text += f"• @{u.username} (ID: `{u.telegram_id}`)\n"

    await update.message.reply_text(text, parse_mode='Markdown')
    db.close()


# ========== ОБРАБОТЧИК СООБЩЕНИЙ ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает все входящие сообщения"""
    # Проверяем доступ (для всех сообщений, кроме публичных команд)
    if update.message.text and update.message.text.startswith('/'):
        command = update.message.text.split()[0].lower()
        if command in PUBLIC_COMMANDS:
            # Публичные команды пропускаем без проверки
            return

    if not await check_access(update, context):
        return

    # Если пользователь в белом списке - отвечаем
    await update.message.reply_text(
        "✅ Вы авторизованы! Я буду присылать вам уведомления о сертификатах."
    )


# ========== РЕГИСТРАЦИЯ НОВЫХ ПОЛЬЗОВАТЕЛЕЙ ==========
async def register_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Автоматически регистрирует пользователя, если он написал боту"""
    user = update.effective_user
    db: Session = next(get_db())

    if not TelegramUserDB.user_exists(db, user.id):
        # Добавляем в БД
        username = user.username or f"user_{user.id}"
        TelegramUserDB.add_user(
            db,
            telegram_id=user.id,
            username=username,
            chat_id=user.id
        )
        logger.info(f"New user registered: @{username} (ID: {user.id})")

        await update.message.reply_text(
            "✅ Вы успешно зарегистрированы в системе!\n"
            "Теперь вы будете получать уведомления о сертификатах."
        )
    db.close()


# ========== ЗАПУСК БОТА ==========
def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Публичные команды (доступны всем)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("register", register))

    # Админ команды
    application.add_handler(CommandHandler("add_user", add_user))
    application.add_handler(CommandHandler("remove_user", remove_user))
    application.add_handler(CommandHandler("list_users", list_users))

    # Обработчик новых пользователей (всегда доступен)
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        register_new_user
    ))

    # Обработчик всех остальных сообщений (с проверкой доступа)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    # Запускаем бота
    print("🤖 Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()