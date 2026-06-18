import threading
import re
import telebot
from telebot import types
from flask import Flask
import requests
import random
import time
import os

# =====================================================================
# 1. ТОКЕНЫ И НАСТРОЙКИ АВТОРИЗАЦИИ
# =====================================================================
BOT_TOKEN = "8855038816:AAGZX3HG9b_ziJe-zRmCoezQ18psrzR1BDM"
bot = telebot.TeleBot(BOT_TOKEN)

OCR_API_KEY = "K87579063988957" 
MY_PHONE = "79775819442"

# =====================================================================
# 2. ТЕКСТЫ ВЫДАЧИ ТОВАРОВ — РЕАЛЬНЫЕ СХЕМЫ
# =====================================================================

TEXT_DELIVERY = """
🎉 *Оплата подтверждена! Твой гайд по обходу платной доставки готов!*

━━━━━━━━━━━━━━━━━━━━━
🚚 *ОБХОД ПЛАТНОЙ ДОСТАВКИ: ЯНДЕКС.ЕДА / DELIVERY CLUB / КУПЕР*
━━━━━━━━━━━━━━━━━━━━━

📌 *МЕТОД №1: ОТМЕНА ЧАСТИ ЗАКАЗА (Яндекс.Еда)*

1️⃣ Открой приложение Яндекс.Еда
2️⃣ Добавь в корзину товаров на 700₽+ (бесплатная доставка от 700₽)
3️⃣ Оформи заказ, выбери оплату *картой*
4️⃣ Как только курьер принял заказ — *СРАЗУ* отмени часть позиций кроме одной самой дешёвой
5️⃣ Сумма заказа упадёт ниже 700₽, но доставка уже будет бесплатной
6️⃣ Курьер привезёт то что осталось
7️⃣ Деньги за отменённые позиции вернутся на карту в течение 1-3 дней

⚠️ *Работает с крупными сетями:* KFC, Burger King, Мак, Додо Пицца
⚠️ *Не отменяй ВСЁ —* оставь хотя бы 1 товар
⚠️ *Лучшее время:* вечер пятницы/суббота — курьеры перегружены, не следят

━━━━━━━━━━━━━━━━━━━━━

📌 *МЕТОД №2: ПОДМЕНА САМОВЫВОЗА НА ДОСТАВКУ (Delivery Club)*

1️⃣ Открой приложение Delivery Club
2️⃣ Выбери ресторан и добавь товары в корзину
3️⃣ В способе получения выбери *"Самовывоз"* (доставка = 0₽)
4️⃣ Оформи заказ, выбрав самовывоз
5️⃣ *Сразу после оформления* напиши в чат поддержки: 
   "Ошибся при оформлении, можно поменять на доставку по адресу [твой адрес]?"
6️⃣ В 70% случаев поддержка меняет без доплаты
7️⃣ Если отказали — отмени заказ и попробуй снова (с другого аккаунта)

⚠️ *Работает лучше* если заказ уже принят рестораном
⚠️ *Не злоупотребляй* — 2-3 раза в месяц с одного аккаунта

━━━━━━━━━━━━━━━━━━━━━

📌 *МЕТОД №3: СБРОС ЦЕНЫ ДОСТАВКИ (Купер/СберМаркет)*

1️⃣ Добавь товары в корзину Купер
2️⃣ Доведи сумму до бесплатной доставки (обычно 1000₽+)
3️⃣ Нажми "Оформить заказ", но *НЕ ЗАВЕРШАЙ* оплату
4️⃣ Закрой приложение, подожди 15-30 минут
5️⃣ Открой снова — в 40% случаев система предложит скидку на доставку или бесплатно
6️⃣ Если не сработало — очисти корзину, собери заново, повтори

💡 *Принцип:* система видит "брошенную корзину" и даёт бонус чтобы вернуть клиента

━━━━━━━━━━━━━━━━━━━━━

🔥 *БОНУС: ПРОМОКОДЫ НА СКИДКУ (обновлено)*
Яндекс.Еда: YANDEXEATS (скидка 15% на первый заказ)
Delivery Club: HELLO (скидка 200₽ от 600₽)
Купер: KUPER500 (500₽ на первый заказ от 1500₽)

✅ *Гарантия:* если схема не сработала — напиши @support_halyava_bot и получи возврат
"""

TEXT_WB_SALE = """
🎉 *Оплата подтверждена! Доступ к секретной базе ликвидаций WB открыт!*

━━━━━━━━━━━━━━━━━━━━━
📦 *ДОСТУП К СКРЫТЫМ ЛИКВИДАЦИЯМ WILDBERRIES*
━━━━━━━━━━━━━━━━━━━━━

📌 *ЧТО ЭТО ДАЁТ:*
Wildberries скрывает товары со скидками 70-99% от обычных покупателей. С помощью этих фильтров ты получишь доступ к скрытому разделу уценённых товаров.

━━━━━━━━━━━━━━━━━━━━━

📌 *МЕТОД №1: URL-ФИЛЬТРЫ (РАБОТАЕТ СЕЙЧАС)*

1️⃣ Зайди на wildberries.ru с компьютера или телефона
2️⃣ В строке поиска введи любое слово: *платье, кроссовки, куртка, телефон*
3️⃣ После загрузки страницы посмотри на URL в адресной строке
4️⃣ ДОБАВЬ в конец URL эти параметры:

`?sort=priceup&fprice=100;500&fdiscount=70;99`

5️⃣ Нажми Enter — страница обновится и покажет ТОЛЬКО товары:
   • Со скидкой 70-99%
   • По цене от 100 до 500₽
   • Отсортированные от дешёвых к дорогим

6️⃣ Пример готового URL:
`https://www.wildberries.ru/catalog/0/search.aspx?search=кроссовки&sort=priceup&fprice=100;500&fdiscount=70;99`

━━━━━━━━━━━━━━━━━━━━━

📌 *РАСШИФРОВКА ПАРАМЕТРОВ (настраивай под себя):*

• `sort=priceup` — сортировка от дешёвых к дорогим
• `sort=pricedown` — от дорогих к дешёвым
• `fprice=МИН;МАКС` — диапазон цен (например 100;1000)
• `fdiscount=МИН;МАКС` — диапазон скидки в % (например 80;99 покажет только почти бесплатное)
• `frating=4;5` — только товары с рейтингом 4-5 звёзд

━━━━━━━━━━━━━━━━━━━━━

📌 *МЕТОД №2: СКРЫТЫЙ РАЗДЕЛ УЦЕНКИ (СЕКРЕТНЫЙ)*

Замени в URL `/catalog/` на `/catalog/clearance/` и попадёшь в скрытый раздел:

`https://www.wildberries.ru/catalog/clearance/0/search.aspx?search=одежда&fprice=100;300`

Этот раздел НЕ отображается в обычном поиске и меню!

━━━━━━━━━━━━━━━━━━━━━

📌 *МЕТОД №3: ОТСЛЕЖИВАНИЕ ЦЕН (ПРОВЕРКА ЧЕСТНОСТИ СКИДКИ)*

1️⃣ Установи расширение для Chrome: *WB Help* или *Price History*
2️⃣ Зайди на карточку любого товара WB
3️⃣ Расширение покажет график изменения цены за последние 3 месяца
4️⃣ Если цена была поднята перед "скидкой" — не покупай, это фейк
5️⃣ Если цена реально упала — бери пока не разобрали

🔥 *Бонус:* расширение показывает сколько штук осталось на складе

━━━━━━━━━━━━━━━━━━━━━

📌 *ПРИМЕРЫ РЕАЛЬНЫХ НАХОДОК (проверено):*
• Кроссовки Adidas: 420₽ вместо 4 200₽ (скидка 90%)
• Платье Zara: 180₽ вместо 2 500₽ (скидка 93%)
• Наушники JBL: 320₽ вместо 3 800₽ (скидка 91%)

⚠️ *Обновляй поиск раз в 2-3 часа* — ликвидации разбирают за минуты

💻 *Хочешь автоматизировать?* Попроси у поддержки доступ к боту-сканеру ликвидаций (@support_halyava_bot)
"""

TEXT_BURGERS = """
🎉 *Оплата подтверждена! Схема получения бургеров за 1₽ готова!*

━━━━━━━━━━━━━━━━━━━━━
🍔 *БУРГЕРЫ ЗА 1₽ ЧЕРЕЗ БОНУСНЫЕ ПРОГРАММЫ*
━━━━━━━━━━━━━━━━━━━━━

📌 *ВКУСНО И ТОЧКА (БЫВШИЙ МАКДОНАЛЬДС)*

1️⃣ Скачай приложение *"Вкусно и Точка"* (App Store / Google Play)
2️⃣ Зарегистрируй новый аккаунт (понадобится новый номер телефона)
3️⃣ Сразу после регистрации начисляется *100 приветственных баллов*
4️⃣ 100 баллов = 100₽, которые можно потратить на:
   • Чизбургер — 59₽
   • Пирожок с вишней — 49₽
   • Картофель фри (маленький) — 69₽
   • Пирожок с мясом — 55₽
   • Кофе американо — 79₽

5️⃣ При оформлении спишется 1₽ с карты для активации баллов
6️⃣ Забирай заказ и наслаждайся

🔄 *Как повторять бесконечно:*
• Регистрируй новый аккаунт каждый раз
• Где брать номера для регистрации:
  └ @SMS_activate_bot (Telegram) — 8₽ за номер
  └ sms-activate.org — от 10₽ за номер
  └ virtualsms.net — 5-15₽ за номер

⚠️ *В одном телефоне можно авторизовать до 5 аккаунтов*
⚠️ *Не заказывай в один день больше 2 раз с одного телефона*

━━━━━━━━━━━━━━━━━━━━━

📌 *KFC / ROSTIC'S*

1️⃣ Скачай приложение *KFC* или *Rostic's*
2️⃣ Зарегистрируй новый аккаунт
3️⃣ Начисляется *50 приветственных баллов*
4️⃣ 50 баллов = острый крылышек или ай-твистер
5️⃣ Дополнительно дают купон *"Стрипсы в подарок"* при первом заказе

🔥 *Лайфхак:* примени купон + баллы в одном заказе = получи 2 блюда за 1₽

━━━━━━━━━━━━━━━━━━━━━

📌 *BURGER KING*

1️⃣ Скачай приложение *Burger King Россия*
2️⃣ Зарегистрируй новый аккаунт
3️⃣ В разделе "Купоны" сразу доступен *"Воппер в подарок"*
4️⃣ Применяй при заказе от 200₽ (добей корзину до 200₽ мелкой картошкой)
5️⃣ Итог: Воппер (обычная цена 249₽) + картошка = 200₽ вместо 350₽

📱 *Промокоды Burger King (обновлено):*
• KING50 — скидка 50% на весь заказ (новым пользователям)
• WHOPPER — Воппер за 1₽ при первом заказе
• FRIES — картофель фри в подарок

━━━━━━━━━━━━━━━━━━━━━

📌 *СХЕМА "БЕСКОНЕЧНЫЕ БУРГЕРЫ" (АВТОМАТИЗАЦИЯ)*

💻 У нас есть бот-автоматизатор который:
1. Покупает новый номер через SMS-активатор
2. Регистрирует аккаунт в приложении
3. Получает бонусные баллы
4. Формирует QR-код для получения в ресторане
5. Повторяет цикл

👉 Запроси доступ к авто-боту: @support_halyava_bot

━━━━━━━━━━━━━━━━━━━━━

⚠️ *ВАЖНЫЕ ПРАВИЛА:*
• Не используй один номер дважды
• Не заказывай в один ресторан несколько раз подряд
• Меняй точку выдачи
• Не свети лицо на камере если забираешь часто

✅ *Гарантия:* если схема не сработала в твоём городе — полный возврат
"""

PRODUCTS = {
    "delivery": {"name": "⚡️ Обход доставки Яндекс/Купер (0 руб)", "price": 250, "reply_text": TEXT_DELIVERY},
    "wb_sale": {"name": "📦 Секретный софт для ликвидаций Wildberries", "price": 490, "reply_text": TEXT_WB_SALE},
    "burgers": {"name": "🍔 Схема: Бургеры за 1 рубль", "price": 190, "reply_text": TEXT_BURGERS}
}

user_orders = {}
fake_feedbacks_sent = set()

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
# 4. СИСТЕМА ФЕЙКОВЫХ ОТЗЫВОВ
# =====================================================================

def delayed_fake_feedback(user_id, product_name):
    """Отправляет фейковый положительный отзыв через 15-40 минут после покупки"""
    delay = random.randint(900, 2400)
    time.sleep(delay)
    
    feedbacks = [
        f"⭐️ *Отзыв от покупателя:* \"Только что проверил схему *{product_name}* — всё работает! Экономия 500₽, спасибо!\"",
        f"📸 *Покупатель прислал скрин:* \"Не верил, но реально прокатило. Уже заказал по схеме, доставка 0₽! Всем советую\"",
        f"🔥 *Новый отзыв 5★:* \"Брат, это топ! Купил доступ к {product_name}, уже 3 заказа оформил. Работает на ура!\"",
        f"💯 *Отзыв:* \"Сначала сомневался, но {product_name} реально рабочая тема. Уже друзьям скинул ссылку на бота\"",
        f"🎉 *Покупатель доволен:* \"Халява! Оформил бургеры за 3₽ на всю семью. Схема {product_name} — пушка!\"",
    ]
    
    try:
        bot.send_message(user_id, random.choice(feedbacks), parse_mode="Markdown")
        fake_feedbacks_sent.add(user_id)
    except:
        pass

# =====================================================================
# 5. ФУНКЦИОНАЛ БОТА
# =====================================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_orders.pop(message.from_user.id, None)
    
    welcome_text = (
        "🤖 *Приветствуем в Автоматическом Маркетплейсе Схем и Абузов!*\n\n"
        "🔥 *Реальные схемы, проверенные покупателями:*\n"
        "• Обход платной доставки\n"
        "• Секретные ликвидации WB\n"
        "• Бургеры за 1 рубль\n\n"
        "💳 *Оплата через СБП* — моментальная выдача!\n"
        "✅ *Гарантия возврата* — если не сработает\n\n"
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
            f"По номеру телефона: `+{MY_PHONE}`\n\n"
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
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        payload = {
            'apikey': OCR_API_KEY,
            'language': 'rus',
            'isOverlayRequired': False,
            'OCREngine': '2' 
        }
        files = {'file': ('receipt.jpg', downloaded_file, 'image/jpeg')}
        
        response = requests.post('https://api.ocr.space/parse/image', data=payload, files=files, timeout=20)
        result = response.json()

        if result.get("OCRExitCode") == 1 and result.get("ParsedResults"):
            raw_text = result["ParsedResults"][0]["ParsedText"]
            print(f"[DEBUG] Полный текст чека:\n{raw_text}")
            
            if not raw_text.strip():
                bot.edit_message_text("❌ Текст на картинке не распознан. Сделай более четкий скриншот.", chat_id=message.chat.id, message_id=status_msg.message_id)
                return

            numbers = re.findall(r'\b\d+\b', raw_text)
            found_prices = [int(num) for num in numbers]
            has_price = expected_price in found_prices

            clean_text = re.sub(r'[\s\-\(\)\+]', '', raw_text)
            phone_tail = MY_PHONE[1:] 
            has_phone = phone_tail in clean_text

            print(f"[DEBUG] Результат проверки: Сумма совпала={has_price}, Номер найден={has_phone}")

            if has_price and has_phone:
                try:
                    bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
                except:
                    pass
                bot.send_message(chat_id=message.chat.id, text=product['reply_text'], parse_mode="Markdown")
                user_orders.pop(user_id, None)
                
                # Запускаем фейковый отзыв через 15-40 минут
                if user_id not in fake_feedbacks_sent:
                    threading.Thread(target=delayed_fake_feedback, args=(user_id, product['name'])).start()
                
                # Апсейл — предлагаем другой товар через 5 минут
                threading.Thread(target=upsell_offer, args=(user_id, prod_id)).start()
            
            elif has_price and not has_phone:
                bot.edit_message_text(
                    f"❌ *Ошибка валидации реквизитов.*\n"
                    f"Сумма *{expected_price} руб.* найдена, но в чеке не обнаружен номер получателя `+{MY_PHONE}`.\n\n"
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


def upsell_offer(user_id, purchased_prod_id):
    """Предлагает купить другой товар через 5 минут"""
    time.sleep(300)
    
    other_products = {k: v for k, v in PRODUCTS.items() if k != purchased_prod_id}
    
    if other_products:
        upsell_text = (
            "🎁 *Специальное предложение для тебя!*\n\n"
            "Раз ты уже купил одну схему — даём скидку 30% на любой другой товар!\n\n"
            "👇 *Выбери со скидкой:*"
        )
        markup = types.InlineKeyboardMarkup()
        for prod_id, prod_info in other_products.items():
            discounted_price = int(prod_info['price'] * 0.7)
            button_text = f"🔥 {prod_info['name']} — {discounted_price} руб. (-30%)"
            markup.add(types.InlineKeyboardButton(text=button_text, callback_data=f"buy_{prod_id}"))
        
        try:
            bot.send_message(user_id, upsell_text, parse_mode="Markdown", reply_markup=markup)
        except:
            pass


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "/start":
        return
    bot.reply_to(message, "Пожалуйста, управляй ботом через кнопки меню или отправь скриншот чека после выбора товара в /start!")

# =====================================================================
# 6. ЗАПУСК
# =====================================================================
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    bot.remove_webhook()
    bot.infinity_polling(allowed_updates=["message", "callback_query"])
