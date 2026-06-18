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

# =====================================================================
# 2. ТЕКСТЫ ВЫДАЧИ ТОВАРОВ (МАНУАЛЫ И СХЕМЫ)
# =====================================================================
TEXT_DELIVERY = (
    "🎉 *Оплата подтверждена! Твой мануал по бесплатной доставке готов:*\n\n"
    "Наверняка тебе надоело отдавать по 149–299 рублей за доставку каждого заказа. "
    "Этот метод позволяет полностью обнулить стоимость доставки в Яндекс Еде, Купере "
    "(бывший СберМаркет) и Самокате, даже если на улице повышенный спрос.\n\n"
    "📘 *Инструкция по обузу:*\n"
    "1. Скачай приложение-клонер (если у тебя Android, используй *App Cloner*, если iOS — работаем через инкогнито-вкладку Safari).\n"
    "2. Привяжи виртуальный номер (купи его на любом сервисе смс-активаций за 3–5 рублей).\n"
    "3. Набери корзину, примени промокод на первый заказ (база свежих промокодов обновляется в мануале каждый день).\n"
    "4. *Главный секрет:* На этапе оплаты используй способ, который обнуляет сервисный сбор (подробный алгоритм по ссылке ниже).\n\n"
    "🔗 *Ссылка на закрытый гайд (инструкция с картинками):* [ОТКРЫТЬ МАНУАЛ](https://telegra.ph/Polnyj-gajd-po-dostavke-primer)\n"
    "_Сохрани ссылку, доступ однократный!_"
)

TEXT_WB_SALE = (
    "🎉 *Оплата подтверждена! Доступ к WB-Ликвидациям открыт:*\n\n"
    "Продавцы на Wildberries постоянно совершают ошибки при заведении карточек или сливают остатки "
    "складов за копейки, чтобы не платить за хранение. Обычный человек эти товары никогда не увидит — "
    "их за секунды скупают боты. Теперь такой бот есть и у тебя.\n\n"
    "🤖 *Что ты получаешь:*\n"
    "1. Ссылку на закрытый Telegram-канал/парсер, куда наш софт каждую минуту выгружает товары с реальной скидкой от 70% до 95%.\n"
    "2. Готовый скрипт-автореггер для ПК, который может автоматически мониторить твою корзину.\n\n"
    "🛠 *Как запустить:*\n"
    "* Перейди по ссылке ниже.\n"
    "* Изучи правила настройки фильтров (чтобы тебе не летел спам, а только топовые вещи: электроника, одежда).\n"
    "* Успевай нажимать кнопку «Купить» быстрее остальных!\n\n"
    "🔗 *Твоя персональная ссылка на вход и софт:* [АКТИВИРОВАТЬ ДОСТУП](https://telegra.ph/Dostup-k-softu-WB-primer)"
)

TEXT_BURGERS = (
    "🎉 *Оплата подтверждена! Твой сытный мануал здесь:*\n\n"
    "Схема основана на легальном обузе приветственных бонусов ресторанов быстрого питания и систем "
    "лояльности крупных банков. При правильном подходе ты сможешь обедать со скидкой до 99% каждый день.\n\n"
    "🍔 *Краткая суть схемы:*\n"
    "1. *Для Вкусно и точка / Ростикс:* Используем связку «Новый аккаунт + Спец-код». Мы даем тебе генератор кодов, который бот принимает за покупку первого заказа. Ты получаешь Бургер или Баскет за 1 рубль.\n"
    "2. *Для БК:* Обуз внутренней игры в приложении + списание партнерских баллов. За 5 минут кликов в симуляторе на новом аккаунте начисляется до 300 корон.\n\n"
    "🔗 *Полная пошаговая схема со всеми кодами:* [ЗАБРАТЬ СХЕМУ НА ЕДУ](https://telegra.ph/Shema-na-burgery-primer)\n\n"
    "_Приятного аппетита! Нажми /start, если захочешь купить другие схемы._"
)

# Каталог доступных товаров и цен
PRODUCTS = {
    "delivery": {"name": "⚡️ Обход доставки Яндекс/Купер (0 руб)", "price": 250, "reply_text": TEXT_DELIVERY},
    "wb_sale": {"name": "📦 Секретный софт для ликвидаций Wildberries", "price": 490, "reply_text": TEXT_WB_SALE},
    "burgers": {"name": "🍔 Схема: Бургеры за 1 рубль", "price": 190, "reply_text": TEXT_BURGERS}
}

# Память для фиксации выбора пользователя { user_id: "id_товара" }
user_orders = {}

# =====================================================================
# 3. ВЕБ-СЕРВЕР ДЛЯ ПОДДЕРЖАНИЯ ЖИЗНИ НА RENDER
# =====================================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот активен, шлюз OCR подключен по прямому каналу передачи файлов!"

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
        "Мы полностью автоматизировали выдачу приватных мануалов. Выбирай нужную тему из "
        "каталога ниже, оплачивай по СБП и отправляй скриншот чека прямо в чат. "
        "Система мгновенно распознает платеж и автоматически выдаст тебе ссылку!\n\n"
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
            f"💳 *Реквизиты для оплаты (Сбербанк / СБП):*\n"
            f"По номеру телефона: `+79775819442`\n\n"
            f"⚠️ *Важно:* Переводи точную сумму ({product['price']} руб.). "
            f"После перевода *отправь скриншот чека* прямо в этот чат!"
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=payment_text,
            parse_mode="Markdown"
        )


@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    user_id = message.from_user.id
    
    if user_id not in user_orders:
        bot.reply_to(
            message, 
            "❌ Ты еще не выбрал товар! Напиши /start, выбери схему из списка, "
            "оплати её и только потом присылай чек."
        )
        return

    prod_id = user_orders[user_id]
    product = PRODUCTS[prod_id]
    expected_price = product['price']

    status_msg = bot.reply_to(message, "⏳ Безопасный шлюз считывает данные с чека, подожди пару секунд...")

    try:
        # 1. Скачиваем фото чека напрямую из Telegram в оперативную память (без сохранения на диск)
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # 2. Настраиваем параметры для OCR.Space
        # Используем OCREngine='2', так как он идеально подходит для чеков и скриншотов с телефонов
        payload = {
            'apikey': OCR_API_KEY,
            'language': 'rus',
            'isOverlayRequired': False,
            'OCREngine': '2' 
        }
        
        # Передаем файл в теле запроса
        files = {
            'file': ('receipt.jpg', downloaded_file, 'image/jpeg')
        }
        
        # Отправляем POST-запрос с файлом
        response = requests.post('https://api.ocr.space/parse/image', data=payload, files=files, timeout=20)
        result = response.json()

        # 3. Разбираем ответ от сервера распознавания
        if result.get("OCRExitCode") == 1 and result.get("ParsedResults"):
            raw_text = result["ParsedResults"][0]["ParsedText"]
            print(f"[DEBUG] Текст с чека: {raw_text}")
            
            if not raw_text.strip():
                bot.edit_message_text("❌ Текст на картинке не обнаружен. Попробуй отправить несжатый скриншот или сделай его более четким.", chat_id=message.chat.id, message_id=status_msg.message_id)
                return

            # Вытаскиваем все числа из текста чека
            numbers = re.findall(r'\b\d+\b', raw_text)
            found_prices = [int(num) for num in numbers]
            print(f"[DEBUG] Найденные числа на чеке: {found_prices}")

            # 4. Проверяем цену
            if expected_price in found_prices:
                try:
                    bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
                except:
                    pass
                
                # Отправляем пользователю купленный им мануал
                bot.send_message(chat_id=message.chat.id, text=product['reply_text'], parse_mode="Markdown")
                # Закрываем сессию покупки
                user_orders.pop(user_id, None)
            else:
                bot.edit_message_text(
                    f"❌ *Сумма не найдена.*\n"
                    f"Система хочет увидеть на чеке число *{expected_price}*, но среди найденных чисел его нет.\n\n"
                    f"Убедись, что на скриншоте четко видна сумма перевода.",
                    chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown"
                )
        else:
            error_details = result.get("ErrorMessage", "Неизвестная ошибка шлюза")
            print(f"[OCR ERROR DETAILS]: {error_details}")
            bot.edit_message_text("❌ Не удалось считать текст. Пожалуйста, сделай другой скриншот чека.", chat_id=message.chat.id, message_id=status_msg.message_id)

    except Exception as e:
        print(f"[ERROR MAIN]: {e}")
        bot.edit_message_text("❌ Ошибка соединения со шлюзом проверки. Попробуй еще раз через минуту.", chat_id=message.chat.id, message_id=status_msg.message_id)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "/start":
        return
    bot.reply_to(message, "Пожалуйста, управляй ботом через кнопки меню или отправь скриншот чека после выбора товара в /start!")

# =====================================================================
# 5. ЗАПУСК ПОТОКОВ
# =====================================================================
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    bot.remove_webhook()
    print("Бот успешно запущен на легких сетевых запросах!")
    bot.infinity_polling(allowed_updates=["message", "callback_query"])
