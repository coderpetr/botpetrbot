import os
import threading
import telebot
from flask import Flask
from google import genai
from google.genai import types

# =====================================================================
# 1. НАСТРОЙКИ ТОКЕНОВ (Вставь сюда свои ключи)
# =====================================================================
BOT_TOKEN = "8678906227:AAH8jULnc8BDegqwFt-SGH2ytXeVMDAAzZk"
GEMINI_API_KEY = "AQ.Ab8RN6IDCjCtVYzCJUYI_n_jyJIfohbF7c2TePYAlP5iga1Xew"

# Инициализируем клиента Telegram и нейросеть Google
bot = telebot.TeleBot(BOT_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# =====================================================================
# 2. ФЕЙКОВЫЙ ВЕБ-СЕРВЕР ДЛЯ ОБХОДА БЛОКИРОВКИ RENDER (20 минут)
# =====================================================================
app = Flask(__name__)

@app.route('/')
def home():
    # На эту страницу будет заходить Cron-Job.org каждые 5 минут
    return "Бот активен и работает 24/7!"

def run_flask():
    # Render передает порт через переменную окружения PORT, по умолчанию ставим 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# =====================================================================
# 3. ЛОГИКА ТЕЛЕГРАМ-БОТА (РАСПОЗНАВАНИЕ ЧЕКОВ)
# =====================================================================

# Приветственный текст при команде /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "Привет! Я твой автоматический бот-помощник.\n"
        "Отправь мне скриншот чека Сбербанка, и я сразу скажу сумму перевода!"
    )

# Обработчик входящих фотографий (чеков)
@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    try:
        # Отправляем промежуточный статус пользователю
        status_msg = bot.reply_to(message, "⏳ Распознаю чек, подожди пару секунд...")

        # Скачиваем самую большую (качественную) версию фото из сообщения
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Конвертируем байты фотографии для отправки в Gemini
        image_part = types.Part.from_bytes(
            data=downloaded_file,
            mime_type='image/jpeg'
        )

        # Строгий промпт-инструкция для искусственного интеллекта
        prompt = (
            "Ты — эксперт по распознаванию финансовых документов. Перед тобой скриншот чека "
            "или успешного перевода из банковского приложения (например, Сбербанк). "
            "Внимательно найди финальную сумму операции (она обычно идет после слов 'Сумма', "
            "'Сумма перевода', 'Размер платежа' или указана крупным шрифтом с символом рубля ₽).\n"
            "Выведи ТОЛЬКО эту сумму цифрами. Если есть копейки, укажи их через точку (например, 500 или 1250.50).\n"
            "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать буквы, валюту (руб, ₽), пробелы между цифрами (пиши 10000 вместо 10 000) "
            "или любые другие пояснения. Если на картинке вообще нет чека или невозможно найти сумму, "
            "напиши ровно одно слово: ОШИБКА"
        )

        # Делаем запрос к легкой и быстрой модели Gemini 2.5 Flash
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_part, prompt]
        )

        # Очищаем ответ от случайных пробелов или переносов строк
        result_text = response.text.strip()
        print(f"[DEBUG] Gemini ответила на чек: '{result_text}'")
        # Проверяем, справилась ли нейросеть
        if "ОШИБКА" in result_text or not result_text:
            bot.edit_message_text(
                "❌ Не удалось распознать сумму на этом чеке. Убедись, что это чек Сбера и фото четкое.", 
                chat_id=message.chat.id, 
                message_id=status_msg.message_id
            )
        else:
            # Успех! Переменная result_text хранит чистую сумму (например, 500)
            # Здесь ты можешь дописать логику начисления баланса в базу данных
            bot.edit_message_text(
                f"✅ Чек успешно распознан!\nСумма платежа: *{result_text}* руб.", 
                chat_id=message.chat.id, 
                message_id=status_msg.message_id,
                parse_mode="Markdown"
            )

    except Exception as e:
        print(f"Ошибка при обработке фотографии: {e}")
        bot.reply_to(message, "Произошла внутренняя ошибка при чтении фото. Попробуй позже.")

# =====================================================================
# 4. ЗАПУСК ВСЕЙ СИСТЕМЫ
# =====================================================================
if __name__ == '__main__':
    print("Старт фонового веб-сервера для Render...")
    # Запускаем Flask в отдельном потоке, чтобы он не мешал боту слушать сообщения
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("Старт Telegram бота...")
    # Запускаем бесконечный опрос серверов Телеграма
    bot.infinity_polling()
