import logging
import os
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from sheets_api import append_task
from ai import transcribe_audio, extract_text_from_image
from config import TELEGRAM_BOT_TOKEN

# ---- Логування ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ---- Допоміжні ----
def _buf(context: ContextTypes.DEFAULT_TYPE) -> list:
    return context.user_data.setdefault("buffer", [])

def _kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆕 Створити задачу", callback_data="new_task")],
        [InlineKeyboardButton("🧹 Очистити чернетку", callback_data="clear_buf")],
    ])

# ---- Команди ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Надсилай текст / голос / фото — я збиратиму їх у чернетку.\n"
        "Коли будеш готовий — натисни кнопку нижче, щоб створити одну задачу.",
        reply_markup=_kb()
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот працює!")

# ---- Текст ----
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return
    _buf(context).append(text)
    await update.message.reply_text(
        "💾 Додано до чернетки. Коли завершиш — натисни кнопку.",
        reply_markup=_kb()
    )

# ---- Голос/аудіо ----
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("🎙️ Отримано голос/аудіо")
    voice_or_audio = update.message.voice or update.message.audio
    if not voice_or_audio:
        await update.message.reply_text("⚠️ Не вдалося отримати аудіофайл.")
        return

    file = await voice_or_audio.get_file()
    file_path = "voice_input.ogg"
    await file.download_to_drive(file_path)
    try:
        text = transcribe_audio(file_path)  # синхронний виклик із ai.py
        logger.info(f"🎧 Розпізнаний текст: {text}")
        _buf(context).append(text)
        await update.message.reply_text(f"🧠 Розпізнано текст:\n\n{text}", reply_markup=_kb())
    except Exception as e:
        logger.exception("Помилка розпізнавання аудіо")
        await update.message.reply_text(f"❌ Помилка розпізнавання аудіо: {e}", reply_markup=_kb())
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ---- Фото ----
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("📸 Отримано зображення")
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = "photo_input.jpg"
    await file.download_to_drive(file_path)
    try:
        text = extract_text_from_image(file_path)  # синхронний виклик із ai.py
        logger.info(f"🖼️ OCR текст: {text}")
        _buf(context).append(text)
        await update.message.reply_text(f"📄 Розпізнаний текст:\n\n{text}", reply_markup=_kb())
    except Exception as e:
        logger.exception("Помилка OCR")
        await update.message.reply_text(f"❌ Помилка OCR: {e}", reply_markup=_kb())
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# ---- Кнопки ----
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    buf = _buf(context)

    if q.data == "clear_buf":
        buf.clear()
        await q.edit_message_text("🧹 Чернетку очищено.")
        return

    if q.data == "new_task":
        if not buf:
            await q.edit_message_text("⚠️ Чернетка порожня. Спочатку надішли повідомлення.")
            return
        description = "\n".join(buf)
        try:
            append_task(name="Задача", description=description, tag="#інше")
            await q.edit_message_text("✅ Створено одну задачу з усіх повідомлень.")
        except Exception:
            logger.exception("Помилка запису в Sheets")
            await q.edit_message_text("❌ Помилка збереження у таблицю.")
        finally:
            buf.clear()

# ---- Запуск через webhook ----
def main():
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("❌ Вкажи TELEGRAM_BOT_TOKEN у config.py або як змінну середовища")

    print(f"Python: {sys.version}")
    print("🚀 Бот (webhook) запущено. Очікую вхідні HTTP-запити від Telegram...")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # реєструємо всі твої хендлери
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(buttons))

    # порт надає хостинг (Render/Railway) через змінну PORT
    port = int(os.environ.get("PORT", "8080"))

    # якщо знаєш свій публічний URL під час старту — вкажи тут, і вебхук виставиться автоматично
    external_url = os.environ.get("EXTERNAL_URL")  # наприклад: https://your-app.onrender.com
    webhook_path = os.environ.get("WEBHOOK_PATH", "webhook")  # без початкового слеша
    secret_token = os.environ.get("WEBHOOK_SECRET")  # опційно: додаткова перевірка від Telegram

    if external_url:
        # Telegram одразу отримає адресу вебхука
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=webhook_path,
            webhook_url=f"{external_url.rstrip('/')}/{webhook_path}",
            secret_token=secret_token
        )
    else:
        # якщо external_url невідомий під час старту (типова ситуація на Render),
        # просто піднімаємо сервер; вебхук поставимо вручну після деплою
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=webhook_path,
            secret_token=secret_token
        )

if __name__ == "__main__":
    main()
