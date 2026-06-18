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
# 2. ФЕЙКОВЫЙ ВЕБ-СЕРВЕР ДЛЯ ОБХОДА БЛОКИРОВКИ RENDER (ПИНГЕР)
# =====================================================================
app = Flask(__name__)

@app.route('/')
def home():
    # На эту страницу будет заходить Cron-Job.org каждые 5 минут
    return "Бот активен и работает 24/7!"

def run_flask():
    # Render передает порт через переменную окружения PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# =====================================================================
# 3. ЛОГИКА ТЕЛЕГРАМ-БОТА
# =====================================================================

# Красивое презентационное приветствие при команде /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 *Добро пожаловать в Маркетплейс Схем и Абузов!*\n\n"
        "Я — твой автоматический помощник. Здесь ты найдешь закрытые "
        "мануалы, обходы платной доставки Яндекс/Купер, скрытые ликвидации "
        "складов Wildberries со скидками до 90% и темы на бургеры за 1 рубль.\n\n"
        "💳 *Как начать работу:*\n"
        "1. Отправь мне чистый *скриншот чека Сбербанка* об оплате доступа.\n"
        "2. Наша нейросеть моментально проверит платеж в автоматическом режиме.\n"
        "3. Баланс зачислится на твой аккаунт, и ты получишь ссылки на приватные гайды.\n\n"
        "📸 *Просто прикрепи фото (скриншот) чека прямо в этот чат!*"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")


# Обработчик входящих фотографий (чеков) с защитой от падения
@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    try:
        status_msg = bot.reply_to(message, "⏳ Распознаю чек, подожди пару секунд...")

        # Скачиваем самую качественную версию фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Конвертируем байты фотографии для отправки в Gemini
        image_part = types.Part.from_bytes(
            data=downloaded_file,
            mime_type='image/jpeg'
        )

        # Жесткая и точная инструкция для нейросети
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

        # Изолированный запрос к нейросети Google, чтобы бот не "глох" при сбоях API
        try:
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[image_part, prompt]
            )
            result_text = response.text.strip()
            print(f"[DEBUG] Gemini ответила на чек: '{result_text}'")
        except Exception as ai_error:
            print(f"[КРИТИЧЕСКАЯ ОШИБКА GEMINI API]: {ai_error}")
            bot.edit_message_text(
                "❌ Ошибка нейросети Google: Сервер временно недоступен или сработал гео-блок. Попробуй позже.",
                chat_id=message.chat.id, 
                message_id=status_msg.message_id
            )
            return

        # Проверяем, что вернула нейросеть
        if "ОШИБКА" in result_text or not result_text:
            bot.edit_message_text(
                "❌ Не удалось распознать сумму на этом чеке. Убедись, что это полный скриншот чека Сбера и фото четкое.", 
                chat_id=message.chat.id, 
                message_id=status_msg.message_id
            )
        else:
            # Успех! Переменная result_text хранит чистую сумму
            bot.edit_message_text(
                f"✅ Чек успешно распознан!\nСумма платежа: *{result_text}* руб.\n\nДоступ открыт!", 
                chat_id=message.chat.id, 
                message_id=status_msg.message_id,
                parse_mode="Markdown"
            )

    except Exception as e:
        print(f"Общая ошибка при обработке фото: {e}")
        bot.reply_to(message, "Произошла внутренняя ошибка при чтении фото.")


# Ответ-подсказка на любой другой случайный текст, чтобы бот не молчал
@bot.message_handler(content_types=['text'])
def handle_text(message):
    # Игнорируем команду /start, так как для неё есть отдельный обработчик выше
    if message.text == "/start":
        return
        
    bot.reply_to(
        message, 
        "Я умею работать только по инструкции. 😉\n\n"
        "Пожалуйста, отправь мне *СКРИНШОТ чека Сбербанка* как фотографию, "
        "чтобы нейросеть автоматически проверила оплату и открыла тебе доступ!",
        parse_mode="Markdown"
    )

# =====================================================================
# 4. ЗАПУСК ВСЕЙ СИСТЕМЫ
# =====================================================================
if __name__ == '__main__':
    print("Старт фонового веб-сервера для Render...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("Старт Telegram бота...")
    bot.infinity_polling()
