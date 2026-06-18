import telebot
from telebot import types
import random
import requests


import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Бот онлайн!"

def run_web():
    # Render сам передает нужный порт в переменные окружения
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
# ==================== НАСТРОЙКИ БОТА ====================
BOT_TOKEN = '8678906227:AAH8jULnc8BDegqwFt-SGH2ytXeVMDAAzZk'  # Вставь сюда токен от @BotFather
bot = telebot.TeleBot(BOT_TOKEN)

CARD_NUMBER = "+79775819442"  # Номер телефона для СБП или номер карты
BANK_NAME = "Т-Банк"   # Название твоего банка

# Твой ID в Telegram (можно узнать в боте @userinfobot), чтобы админка открывалась только тебе
ADMIN_ID = 123456789  

# ==================== БАЗА ТОВАРОВ И ЛАЙФХАКОВ ====================
PRODUCTS = {
    "🍔 Еда и Фастфуд": {
        "Бургеры за 1 рубль (50 руб)": {
            "price": 50,
            "items": [
                "🎁 **ТВОЙ ЗАКАЗ ВЫПОЛНЕН!**\n\n"
                "📖 **ГАЙД: Как брать комбо-обеды или бургеры за 1 рубль**\n\n"
                "1️⃣ У всех крупных сетей есть мобильные приложения с программой лояльности, где за первую регистрацию начисляют приветственные баллы или дают купоны на позиции за 1 рубль.\n\n"
                "2️⃣ Скачай официальное приложение «Вкусно — и точка» или «Бургер Кинг».\n\n"
                "3️⃣ Зайди на любой сайт СМС-активаций (например, `5sim.net` или `sms-activate.org`) и купи виртуальный номер для нужного приложения. Стоит он всего 3–7 рублей.\n\n"
                "4️⃣ Зарегистрируй новый аккаунт на этот номер, зайди в раздел 'Акции' или 'Купоны' и забери приветственный бонус.\n\n"
                "5️⃣ **ВАЖНО:** Чтобы сделать повторный круг, тебе нужно не просто выйти из аккаунта, а полностью удалить приложение и скачать заново, либо очистить его КЭШ и ДАННЫЕ в настройках телефона. Тогда система не поймет, что это тот же смартфон!"
            ]
        },
        "Обход платной доставки (40 руб)": {
            "price": 40,
            "items": [
                "🎁 **ТВОЙ ЗАКАЗ ВЫПОЛНЕН!**\n\n"
                "📖 **ЛАЙФХАК: Как обходить платную доставку**\n\n"
                "🔹 **Способ для Купера/Мегамаркета:**\n"
                "Заходи в корзину и добивай сумму заказа любыми дешевыми товарами (например, фирменными пакетами по 3 рублей) до порога, при котором доставка становится бесплатной. "
                "Когда заказ уйдет в работу и тебе позвонит сборщик из магазина, просто вежливо скажи: *«Ой, я случайно добавил в корзину лишние пакеты, уберите их, пожалуйста, из чека»*. "
                "Сборщик уберет их через свой терминал, итоговая сумма уменьшится, а бесплатная доставка от сервиса останется зафиксированной!\n\n"
                "🔹 **Способ для Яндекс Еды:**\n"
                "Если в приложении горит 'Повышенный спрос' и доставка стоит 299 рублей, зайди на сайт Яндекс Еды через браузер на компе (или включи в мобильном браузере режим 'Версия для ПК') в режиме Инкогнито. "
                "Веб-алгоритмы Яндекса часто обнуляют стоимость доставки для 'новых' браузеров, чтобы привлечь клиента, пока приложение пытается содрать максимум."
            ]
        }
    },
    "🛍 Маркетплейсы": {
        "Секретные скидки Wildberries (60 руб)": {
            "price": 60,
            "items": [
                "🎁 **ТВОЙ ЗАКАЗ ВЫПОЛНЕН!**\n\n"
                "📖 **МАНУАЛ: Скрытые скидки до 90% на WB и Ozon**\n\n"
                "1️⃣ **Метод «Брошенная корзина»:**\n"
                "Закинь нужный товар в корзину и не оплачивай его 2–3 дня. В панели продавца отображается статистика брошенных корзин, и алгоритмы площадки сами предлагают продавцу выдать автоматическую персональную скидку тем, кто сомневается. Через пару дней цена на этот товар для тебя снизится, и прилетит пуш.\n\n"
                "2️⃣ **Метод поиска ликвидаций:**\n"
                "Вбивай в поисковую строку маркетплейса точные фразы: *«Ликвидация остатков»*, *«Утилизация склада»*, *«Брак упаковки»*. Продавцы, у которых заканчивается оплаченный период хранения на складах WB, сливают новые товары за копейки, чтобы не платить за утилизацию. В обычную выдачу эти карточки не попадают, их нужно искать руками по этим ключам."
            ]
        }
    },
    "🎵 Музыка и Кино": {
        "Музыка без ограничений (40 руб)": {
            "price": 40,
            "items": [
                "🎁 **ТВОЙ ЗАКАЗ ВЫПОЛНЕН!**\n\n"
                "📖 **ИНСТРУКЦИЯ: Бесплатная музыка без рекламы**\n\n"
                "🎵 **Для Яндекс Музыки:**\n"
                "Не плати за подписку на телефоне. Открой мобильный браузер (Safari, Chrome), зайди на сайт Яндекс Музыки и в настройках браузера нажми **'Запросить настольный веб-сайт' (Версия для ПК)**. На ПК-версии сайта Яндекс полностью отключает ограничения на переключение треков и не просит подписку. Слушай сколько влезет.\n\n"
                "🎵 **Для VK Музыки:**\n"
                "Ограничение в 30 минут фонового прослушивания легко обходится. Создай свой приватный Telegram-канал. Воспользуйся бесплатным ботом вроде `@vkmusic_bot`, чтобы скачать свои любимые треки в формате MP3 прямо в Telegram. Перешли их в свой канал. В Телеграме встроен идеальный плеер, который работает в фоне, кэширует музыку без интернета и вообще не имеет рекламы."
            ]
        }
    }
}

# Временная память для заказов пользователей в текущей сессии
user_orders = {}

# ==================== ЛОГИКА БОТА ====================

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for category in PRODUCTS.keys():
        markup.add(types.KeyboardButton(category))
    
    bot.send_message(
        message.chat.id, 
        "🤖 **Добро пожаловать в маркетплейс лайфхаков!**\n\nВыбери категорию товара в меню ниже 👇", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text

    # СЕКРЕТНАЯ АДМИН-ПАНЕЛЬ С КОЛИЧЕСТВОМ ТОВАРОВ
    if text == "/admin":
        if chat_id == ADMIN_ID:
            stats = "📊 **Статистика маркетплейса:**\n\n"
            for category, p_dict in PRODUCTS.items():
                stats += f"📂 Категория: {category}\n"
                for p_name, p_data in p_dict.items():
                    count = len(p_data["items"])
                    stats += f" ├ {p_name} — в наличии: {count} шт.\n"
            bot.send_message(chat_id, stats, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "Маркетплейс работает в штатном режиме. Используй меню.")
        return

    # 1. Обработка выбора категории
    if text in PRODUCTS:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for product_name in PRODUCTS[text].keys():
            markup.add(types.KeyboardButton(product_name))
        markup.add(types.KeyboardButton("⬅️ В главное меню"))
        
        bot.send_message(chat_id, f"Выбрана категория: *{text}*. Выбери товар:", reply_markup=markup, parse_mode="Markdown")
        return

    # 2. Кнопка возврата
    if text == "⬅️ В главное меню":
        start(message)
        return

    # 3. Обработка нажатия на конкретный товар
    selected_product = None
    selected_category = None
    
    for category, p_dict in PRODUCTS.items():
        if text in p_dict:
            selected_category = category
            selected_product = p_dict[text]
            break

    if selected_product:
        if len(selected_product["items"]) == 0:
            bot.send_message(chat_id, "⚠️ Этот лайфхак временно распродан!")
            return

        price = selected_product["price"]
        secret_code = str(random.randint(1000, 9999))
        
        # Сохраняем информацию о заказе юзера
        user_orders[chat_id] = {
            "category": selected_category,
            "product_name": text,
            "price": price,
            "code": secret_code
        }
        
        pay_text = (
            f"📥 **Оформление заказа: {text}**\n\n"
            f"1. Переведи **{price} рублей** по номеру через СБП:\n`{CARD_NUMBER}`\n"
            f"Банк получателя: **{BANK_NAME}**\n\n"
            f"2. ⚠️ **ОБЯЗАТЕЛЬНО** в сообщении получателю (комментарии к переводу) укажи этот код: `{secret_code}`\n\n"
            f"3. Сделай **скриншот чека** об оплате и **отправь его сюда как ФОТО**. Текстовые сообщения бот автоматически отклоняет!"
        )
        bot.send_message(chat_id, pay_text, parse_mode="Markdown")
        return

    bot.send_message(chat_id, "Пожалуйста, используй кнопки меню для навигации.")

# ==================== ПРОВЕРКА ЧЕКОВ (OCR НЕЙРОСЕТЬ) ====================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    
    if chat_id not in user_orders:
        bot.send_message(chat_id, "Сначала выбери товар в меню!")
        return

    order = user_orders[chat_id]
    price_str = str(order["price"])
    
    bot.send_message(chat_id, f"🔍 Проверяю чек на сумму {price_str} руб. и код {order['code']}... Подожди.")

    try:
        # Скачиваем отправленное фото с серверов Telegram
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        
        # Запрос к бесплатному API распознавания текста OCR
        ocr_url = f"https://api.ocr.space/parse/imageurl?apikey=helloworld&url={file_url}&language=rus"
        response = requests.get(ocr_url).json()
        
        if response.get("ParsedResults"):
            extracted_text = response["ParsedResults"][0]["ParsedText"].lower()
            
            # Проверяем наличие секретного случайного кода и цены на скриншоте
            if order["code"] in extracted_text and (price_str in extracted_text or "руб" in extracted_text):
                # Проверяем, что картинка — это реальный банковский чек, а не подделка
                if any(x in extracted_text for x in ["выполнено", "успешно", "перевод", "зачисление", "tinkoff", "sberbank", "сбербанк"]):
                    
                    # Извлекаем текст лайфхака из базы (используем [0], чтобы товар не удалялся и продавался бесконечно)
                    current_item = PRODUCTS[order["category"]][order["product_name"]]["items"][0]
                    
                    bot.send_message(chat_id, current_item, parse_mode="Markdown")
                    del user_orders[chat_id] # Закрываем активный заказ
                else:
                    bot.send_message(chat_id, "❌ Система безопасности: На скриншоте не найдены маркеры банка (статус 'Успешно' или 'Выполнено').")
            else:
                bot.send_message(chat_id, f"❌ Ошибка. На чеке должен быть четко виден твой уникальный код `{order['code']}` и сумма {price_str} руб.")
        else:
            bot.send_message(chat_id, "Не удалось распознать картинку. Пришли четкий, несжатый скриншот чека.")
            
    except Exception as e:
        bot.send_message(chat_id, "Ошибка шлюза проверки чеков. Попробуй скинуть скриншот еще раз.")

# Запуск постоянной работы бота
print("Магазин лайфхаков успешно запущен и готов к работе...")
bot.polling(none_stop=True)
