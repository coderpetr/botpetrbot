import os
import threading
import telebot
from telebot import types as tg_types
from flask import Flask
from google import genai
from google.genai import types as ai_types

# =====================================================================
# 1. ГОТОВЫЕ ТЕКСТЫ ДЛЯ ВЫДАЧИ ПОСЛЕ ОПЛАТЫ
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
    "🤖 *What ты получаешь:*\n"
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
    "2. *Для Бургер Кинг:* Обуз внутренней игры в приложении + списание партнерских баллов. За 5 минут кликов в симуляторе на новом аккаунте начисляется до 300 корон.\n\n"
    "🔗 *Полная пошаговая схема со всеми кодами:* [ЗАБРАТЬ СХЕМУ НА ЕДУ](https://telegra.ph/Shema-na-burgery-primer)\n\n"
    "_Приятного аппетита! Нажми /start, если захочешь купить другие схемы._"
)

# =====================================================================
# 2. НАСТРОЙКИ ТОКЕНОВ И КАТАЛОГ ТОВАРОВ
# =====================================================================
BOT_TOKEN = "8678906227:AAH8jULnc8BDegqwFt-SGH2ytXeVMDAAzZk"
GEMINI_API_KEY = "AQ.Ab8RN6IDCjCtVYzCJUYI_n_jyJIfohbF7c2TePYAlP5iga1Xew"

bot = telebot.TeleBot(BOT_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Наш каталог товаров: связываем кнопки, цены и готовые тексты выдачи
PRODUCTS = {
    "delivery": {
        "name": "⚡️ Обход доставки Яндекс/Купер (0 руб)",
        "price": 10,
        "reply_text": TEXT_DELIVERY
    },
    "wb_sale": {
        "name": "📦 Секретный софт для ликвидаций Wildberries",
        "price": 10,
        "reply_text": TEXT_WB_SALE
    },
    "burgers": {
        "name": "🍔 Схема: Бургеры за 1 рубль в сетевых рестах",
        "price": 10,
        "reply_text": TEXT_BURGERS
    }
}

# Временная память сервера: { user_id: "id_товара" }
user_orders = {}

# =====================================================================
# 3. ФЕЙКОВЫЙ ВЕБ-СЕРВЕР ДЛЯ ОБХОДА БЛОКИРОВКИ RENDER (ПИНГЕР)
# =====================================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот активен и работает 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# =====================================================================
# 4. ЛОГИКА ТЕЛЕГРАМ-БОТА
# =====================================================================

# Главное меню при команде /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 *Приветствуем в Маркетплейсе приватных Схем и Абузов!*\n\n"
        "Мы полностью автоматизировали выдачу товаров. Выбирай интересующую тему из "
        "каталога ниже, оплачивай по указанным реквизитам и отправляй скриншот чека. "
        "Наша нейросеть моментально проверит платеж и сразу выдаст тебе мануал!\n\n"
        "👇 *Выбери товар для покупки:* "
    )
    
    markup = tg_types.InlineKeyboardMarkup()
    for prod_id, prod_info in PRODUCTS.items():
        button_text = f"{prod_info['name']} — {prod_info['price']} руб."
        markup.add(tg_types.InlineKeyboardButton(text=button_text, callback_data=f"buy_{prod_id}"))
        
    bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=markup)


# Обработка нажатий на кнопки товаров
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_payment_selection(call):
    prod_id = call.data.split("_")[1]
    product = PRODUCTS.get(prod_id)
    
    if product:
        user_orders[call.from_user.id] = prod_id
        
        payment_text = (
            f"🛒 *Ты выбрал товар:* {product['name']}\n"
            f"💵 *К оплате строго:* {product['price']} руб.\n\n"
            f"💳 *Реквизиты для оплаты (т-банк):*\n"
            f"`79775819442` (Елена)\n\n"
            f"⚠️ *Важно:* Переводи точную сумму ({product['price']} руб.). "
            f"После перевода *отправь скриншот чека* прямо в этот чат!"
        )
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=payment_text,
            parse_mode="Markdown"
        )


# Обработчик входящих фотографий (чеков)
@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    user_id = message.from_user.id
    
    if user_id not in user_orders:
        bot.reply_to(
            message, 
            "❌ Ты еще не выбрал товар для покупки! Напиши /start, выбери тему из списка, "
            "оплати её и только потом присылай чек."
        )
        return

    prod_id = user_orders[user_id]
    product = PRODUCTS[prod_id]
    expected_price = product['price']

    try:
        status_msg = bot.reply_to(message, "⏳ Нейросеть проверяет твой чек, подожди пару секунд...")

        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        image_part = ai_types.Part.from_bytes(
            data=downloaded_file,
            mime_type='image/jpeg'
        )

        prompt = (
            "Ты — эксперт по распознаванию финансовых документов. Перед тобой скриншот чека "
            "из Сбербанка. Внимательно найди финальную сумму операции.\n"
            "Выведи ТОЛЬКО эту сумму цифрами без лишних слов, пробелов и валюты. "
            "Если на картинке не чек или сумму найти невозможно, напиши: ОШИБКА"
        )

        try:
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[image_part, prompt]
            )
            result_text = response.text.strip()
            print(f"[DEBUG] Gemini ответила: '{result_text}'")
        except Exception as ai_error:
            print(f"[ERROR]: {ai_error}")
            bot.edit_message_text("❌ Ошибка сервера распознавания чеков. Попробуй позже.", chat_id=message.chat.id, message_id=status_msg.message_id)
            return

        if "ОШИБКА" in result_text or not result_text:
            bot.edit_message_text(
                "❌ Не удалось распознать сумму на чеке. Убедись, что скриншот полный и четкий.", 
                chat_id=message.chat.id, message_id=status_msg.message_id
            )
            return

        try:
            if '.' in result_text:
                detected_price = float(result_text)
            else:
                detected_price = int(result_text)
        except ValueError:
            bot.edit_message_text("❌ Ошибка формата суммы. Попробуй сделать скриншот чека заново.", chat_id=message.chat.id, message_id=status_msg.message_id)
            return

        # ПРОВЕРКА СУММЫ ЧЕКА
        if detected_price == expected_price:
            # СУММА СОВПАЛА! Бот удаляет сообщение с загрузкой и присылает готовый текст товара
            bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
            
            # Отправляем тот самый продающий мануал, который привязан к товару
            bot.send_message(chat_id=message.chat.id, text=product['reply_text'], parse_mode="Markdown")
            
            # Очищаем временный заказ из памяти
            user_orders.pop(user_id, None)
        else:
            bot.edit_message_text(
                f"❌ *Ошибка оплаты!*\n"
                f"Выбранный товар стоит *{expected_price} руб.*, а нейросеть обнаружила на чеке сумму *{detected_price} руб.*\n\n"
                f"Пожалуйста, пришли корректный чек об оплате.",
                chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown"
            )

    except Exception as e:
        print(f"Общая ошибка: {e}")
        bot.reply_to(message, "Произошла внутренняя ошибка при чтении фото.")


# Ответ на случайный текст
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "/start":
        return
    bot.reply_to(message, "Пожалуйста, используй кнопки меню или отправь скриншот чека, если ты уже выбрал товар через /start!")


# =====================================================================
# 5. ЗАПУСК
# =====================================================================
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("Бот успешно запущен со всеми товарами!")
    bot.infinity_polling()
