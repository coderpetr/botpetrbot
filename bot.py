import os
import threading
import re
import telebot
from telebot import types
from flask import Flask
from PIL import Image
import pytesseract
import os
# Принудительная установка Tesseract прямо через консоль сервера при старте
print("Проверяем наличие Tesseract OCR в системе...")
if os.system("tesseract --version") != 0:
    print("Tesseract не найден. Устанавливаю системные пакеты...")
    os.system("apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-rus")
# =====================================================================
# 1. НАСТРОЙКИ ТОКЕНОВ И ТОВАРОВ
# =====================================================================
BOT_TOKEN = "8855038816:AAGZX3HG9b_ziJe-zRmCoezQ18psrzR1BDM"
bot = telebot.TeleBot(BOT_TOKEN)

# Тексты выдачи товаров (твои схемы)
TEXT_DELIVERY = (
    "🎉 *Оплата подтверждена! Твой мануал по бесплатной доставке готов:*\n\n"
    "🔗 [ОТКРЫТЬ МАНУАЛ](https://telegra.ph/Polnyj-gajd-po-dostavke-primer)"
)

TEXT_WB_SALE = (
    "🎉 *Оплата подтверждена! Доступ к WB-Ликвидациям открыт:*\n\n"
    "🔗 [АКТИВИРОВАТЬ ДОСТУП](https://telegra.ph/Dostup-k-softu-WB-primer)"
)

TEXT_BURGERS = (
    "🎉 *Оплата подтверждена! Твой сытный мануал здесь:*\n\n"
    "🔗 [ЗАБРАТЬ СХЕМУ НА ЕДУ](https://telegra.ph/Shema-na-burgery-primer)"
)

PRODUCTS = {
    "delivery": {"name": "⚡️ Обход доставки Яндекс/Купер", "price": 10, "reply_text": TEXT_DELIVERY},
    "wb_sale": {"name": "📦 Секретный софт для Wildberries", "price": 10, "reply_text": TEXT_WB_SALE},
    "burgers": {"name": "🍔 Схема: Бургеры за 1 рубль", "price": 10, "reply_text": TEXT_BURGERS}
}

user_orders = {}

# =====================================================================
# 2. ВЕБ-СЕРВЕР (ПИНГЕР)
# =====================================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот активен 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# =====================================================================
# 3. ЛОГИКА БОТА
# =====================================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 *Приветствуем в Маркетплейсе Схем!*\n\n"
        "Выбирай товар, оплачивай и отправляй скриншот чека Сбера. "
        "Система автоматически проверит платеж и выдаст мануал!"
    )
    markup = types.InlineKeyboardMarkup()
    for prod_id, prod_info in PRODUCTS.items():
        button_text = f"{prod_info['name']} — {prod_info['price']} руб."
        markup.add(types.InlineKeyboardButton(text=button_text, callback_data=f"buy_{prod_id}"))
    bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_payment_selection(call):
    prod_id = call.data.split("_")[1]
    product = PRODUCTS.get(prod_id)
    if product:
        user_orders[call.from_user.id] = prod_id
        payment_text = (
            f"🛒 *Товар:* {product['name']}\n"
            f"💵 *Сумма:* {product['price']} руб.\n\n"
            f"💳 *Реквизиты (т-банк):*\n`79775819442`\n\n"
            f"Отправь скриншот чека прямо сюда!"
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=payment_text, parse_mode="Markdown")


@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    user_id = message.from_user.id
    if user_id not in user_orders:
        bot.reply_to(message, "❌ Сначала выбери товар через /start")
        return

    prod_id = user_orders[user_id]
    product = PRODUCTS[prod_id]
    expected_price = product['price']

    status_msg = bot.reply_to(message, "⏳ Считываю данные с чека...")

    try:
        # 1. Скачиваем фото чека во временный файл
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image_path = f"receipt_{user_id}.jpg"
        with open(image_path, "wb") as f:
            f.write(downloaded_file)

        # 2. Локально распознаем текст с картинки с помощью Tesseract
        raw_text = pytesseract.image_to_string(Image.open(image_path), lang='rus+eng')
        
        # Удаляем временный файл сразу после чтения
        if os.path.exists(image_path):
            os.remove(image_path)

        # 3. Ищем регулярным выражением все числа в тексте чека
        # Нам нужны только круглые суммы или суммы с копейками, похожие на цену товара
        numbers = re.findall(r'\b\d+\b', raw_text)
        
        # Переводим все найденные строки в числа
        found_prices = [int(num) for num in numbers]

        print(f"[DEBUG] Распознанный текст: {raw_text}")
        print(f"[DEBUG] Найденные числа: {found_prices}")

        # 4. Проверяем, есть ли цена товара среди найденных на чеке чисел
        if expected_price in found_prices:
            # Успех! Сумма найдена на чеке
            try:
                bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
            except:
                pass
            bot.send_message(chat_id=message.chat.id, text=product['reply_text'], parse_mode="Markdown")
            user_orders.pop(user_id, None)
        else:
            bot.edit_message_text(
                f"❌ *Сумма не найдена.*\n"
                f"Система ищет на чеке число *{expected_price}*, но не видит его.\n"
                f"Убедись, что скриншот четкий и сумма видна.",
                chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown"
            )

    except Exception as e:
        print(f"[ERROR OCR]: {e}")
        bot.edit_message_text("❌ Ошибка обработки изображения. Попробуй еще раз.", chat_id=message.chat.id, message_id=status_msg.message_id)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text != "/start":
        bot.reply_to(message, "Используй кнопки меню или отправь чек после выбора товара в /start!")

# =====================================================================
# 4. ЗАПУСК
# =====================================================================
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    bot.remove_webhook()
    print("Бот на Tesseract OCR запущен!")
    bot.infinity_polling(allowed_updates=["message", "callback_query"])
