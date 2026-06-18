import os
import threading
import re
import telebot
from telebot import types
from flask import Flask
import requests

# =====================================================================
# 1. ТОКЕНЫ И НАСТРОЙКИ АВТОРИЗАЦИИ
# =====================================================================
BOT_TOKEN = "8855038816:AAGZX3HG9b_ziJe-zRmCoezQ18psrzR1BDM"
bot = telebot.TeleBot(BOT_TOKEN)

# Твой рабочий ключ от облачного шлюза распознавания
OCR_API_KEY = "K87579063988957" 

# Твой номер телефона для проверки на чеке (без плюса, чистые цифры для поиска)
MY_PHONE = "79775819442"

# =====================================================================
# 2. ТЕКСТЫ ВЫДАЧИ ТОВАРОВ (МАНУАЛЫ И СХЕМЫ)
# =====================================================================
TEXT_DELIVERY = (
    "🎉 *Оплата подтверждена! Твой мануал по бесплатной доставке готов:*\n\n"
    "🔗 *Ссылка на гайд:* [ОТКРЫТЬ МАНУАЛ](https://telegra.ph/Polnyj-gajd-po-dostavke-primer)"
)

TEXT_WB_SALE = (
    "🎉 *Оплата подтверждена! Доступ к WB-Ликвидациям открыт:*\n\n"
    "🔗 *Твоя ссылка на софт:* [АКТИВИРОВАТЬ ДОСТУП](https://telegra.ph/Dostup-k-softu-WB-primer)"
)

TEXT_BURGERS = (
    "🎉 *Оплата подтверждена! Твой сытный мануал здесь:*\n\n"
    "🔗 *Пошаговая схема со всеми кодами:* [ЗАБРАТЬ СХЕМУ НА ЕДУ](https://telegra.ph/Shema-na-burgery-primer)"
)

PRODUCTS = {
    "delivery": {"name": "⚡️ Обход доставки Яндекс/Купер (0 руб)", "price": 250, "reply_text": TEXT_DELIVERY},
    "wb_sale": {"name": "📦 Секретный софт для ликвидаций Wildberries", "price": 490, "reply_text": TEXT_WB_SALE},
    "burgers": {"name": "🍔 Схема: Бургеры за 1 рубль", "price": 190, "reply_text": TEXT_BURGERS}
}

user_orders = {}

# =====================================================================
# 3. ВЕБ-СЕРВЕР ДЛЯ ПОДДЕРЖАНИЯ ЖИЗНИ НА RENDER
# =====================================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот активен, двойная проверка чеков (Сумма + Номер телефона) включена!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# =====================================================================
# 4. ФУНКЦИОНАЛ И КЛИЕНТСКАЯ ЛОГИКА БОТА
# =====================================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 *Приветствуем в Автоматическом Маркетплейсе Схем и Абузов!*\n\n"
        "Выбирай нужную тему из каталога ниже, оплачивай по СБП и отправляй скриншот чека прямо в чат. "
        "Система автоматически проверит платеж и выдаст тебе ссылку!\n\n"
        "👇 *Выбери товар для покупки:* "
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
            f"🛒 *Ты выбрал товар:* {product['name']}\n"
            f"💵 *К оплате строго:* {product['price']} руб.\n\n"
            f"💳 *Реквизиты для оплаты (СБП):*\n"
            f"По номеру телефона: `+79775819442`\n\n"
            f"⚠️ *Важно:* Переводи точную сумму ({product['price']} руб.). "
            f"После перевода *отправь скриншот чека* прямо в этот чат!"
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

    status_msg = bot.reply_to(message, "⏳ Шлюз безопасности проводит двойную проверку чека...")

    try:
        # 1. Скачиваем фото чека в оперативную память
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # 2. Настраиваем параметры для OCR.Space
        payload = {
            'apikey': OCR_API_KEY,
            'language': 'rus',
            'isOverlayRequired': False,
            'OCREngine': '2' 
        }
        files = {'file': ('receipt.jpg', downloaded_file, 'image/jpeg')}
        
        response = requests.post('https://api.ocr.space/parse/image', data=payload, files=files, timeout=20)
        result = response.json()

        # 3. Разбираем ответ
        if result.get("OCRExitCode") == 1 and result.get("ParsedResults"):
            raw_text = result["ParsedResults"][0]["ParsedText"]
            print(f"[DEBUG] Полный текст чека:\n{raw_text}")
            
            if not raw_text.strip():
                bot.edit_message_text("❌ Текст на картинке не распознан. Сделай более четкий скриншот.", chat_id=message.chat.id, message_id=status_msg.message_id)
                return

            # --- ПРОВЕРКА 1: Поиск суммы ---
            numbers = re.findall(r'\b\d+\b', raw_text)
            found_prices = [int(num) for num in numbers]
            
            has_price = expected_price in found_prices

            # --- ПРОВЕРКА 2: Поиск твоего номера телефона ---
            # Очищаем текст от лишних пробелов, дефисов и скобок, чтобы найти номер в любом виде
            clean_text = re.sub(r'[\s\-\(\)\+]', '', raw_text)
            
            # Ищем совпадение хвоста твоего номера (последние 10 цифр: 9775819442)
            phone_tail = MY_PHONE[1:] 
            has_phone = phone_tail in clean_text

            print(f"[DEBUG] Результат проверки: Сумма совпала={has_price}, Номер найден={has_phone}")

            # 4. Итоговое решение: выдаем товар только если совпало И ТО, И ДРУГОЕ
            if has_price and has_phone:
                try:
                    bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
                except:
                    pass
                bot.send_message(chat_id=message.chat.id, text=product['reply_text'], parse_mode="Markdown")
                user_orders.pop(user_id, None)
            
            elif has_price and not has_phone:
                bot.edit_message_text(
                    f"❌ *Ошибка валидации реквизитов.*\n"
                    f"Сумма *{expected_price} руб.* найдена, но в чеке не обнаружен номер получателя `+79775819442`.\n\n"
                    f"Убедись, что скриншот содержит строку перевода с номером телефона.",
                    chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown"
                )
            else:
                bot.edit_message_text(
                    f"❌ *Сумма не найдена.*\n"
                    f"Система хочет увидеть на чеке число *{expected_price}*, но среди цифр перевода его нет.",
                    chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown"
                )
        else:
            bot.edit_message_text("❌ Не удалось считать данные. Пожалуйста, отправь скриншот чека повторно.", chat_id=message.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        print(f"[ERROR MAIN]: {e}")
        bot.edit_message_text("❌ Временная ошибка проверки. Попробуй отправить скриншот еще раз.", chat_id=message.chat.id, message_id=status_msg.message_id)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "/start":
        return
    bot.reply_to(message, "Пожалуйста, управляй ботом через кнопки меню или отправь скриншот чека после выбора товара в /start!")

# =====================================================================
# 5. ЗАПУСК
# =====================================================================
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    bot.remove_webhook()
    bot.infinity_polling(allowed_updates=["message", "callback_query"])
