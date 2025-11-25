import telebot
from telebot import types
import csv
import os
import time
import threading
from datetime import datetime

# ==========================================
# 👇 ТВОИ НАСТРОЙКИ 👇
TOKEN = '8475081241:AAGRD7eLxKhyLnsu14fch9oq2LtZzVijbkE'
ADMIN_ID = 5431881491
# ==========================================

bot = telebot.TeleBot(TOKEN)
user_data = {} 

# Имена файлов
STATS_FILE = 'statistics.csv'
DB_FILE = 'vuz_database.csv'
SUBS_FILE = 'subscriptions.csv'
PAMYATKA_FILE = 'pamyatka.pdf'

# Синонимы городов
CITY_ALIASES = {
    "питер": "Санкт-Петербург", "спб": "Санкт-Петербург",
    "мск": "Москва", "москва": "Москва",
    "екб": "Екатеринбург", "екат": "Екатеринбург",
    "нижний": "Нижний Новгород",
    "владик": "Владивосток",
    "крас": "Красноярск",
    "крск": "Красноярск",
    "нск": "Новосибирск"
}

# Даты экзаменов 2026 (Проект)
EXAM_DATES = {
    "История/Лит/Хим": "2026-06-01",
    "Русский язык": "2026-06-04",
    "Математика (Б/П)": "2026-06-08",
    "Общество/Физика": "2026-06-11",
    "Био/Гео/Ин.яз": "2026-06-15",
    "Информатика (КЕГЭ)": "2026-06-18"
}

# Справочник профессий
SUBJECTS_INFO = {
    "🧮 Мат + ⚛️ Физ": "**ТЕХНАРЬ-КЛАССИКА:**\n• Строительство\n• Машиностроение\n• Нефтегазовое дело\n• Электроэнергетика\n• Авиастроение",
    "🧮 Мат + 💻 Инф": "**IT-СФЕРА:**\n• Программная инженерия\n• Информационная безопасность\n• Системный анализ\n• Бизнес-информатика",
    "🧬 Био + 🧪 Хим": "**МЕДИЦИНА:**\n• Лечебное дело / Педиатрия\n• Стоматология\n• Фармация\n• Ветеринария\n• Биотехнологии",
    "📚 Общ + 🇬🇧 Инг": "**МЕНЕДЖМЕНТ:**\n• Логистика\n• Управление персоналом\n• Реклама и PR\n• Гостиничное дело",
    "📚 Общ + 📜 Ист": "**ГУМАНИТАРИЙ:**\n• Юриспруденция\n• Политология\n• История\n• Социология"
}

# Текстовые блоки
DOCUMENTS_LIST = """
📂 **СПИСОК ДОКУМЕНТОВ:**
1. Паспорт (скан главной и прописки).
2. Аттестат с приложением (все страницы).
3. СНИЛС (обязательно!).
4. Фотографии 3х4 (матовые, 4-6 шт.).
5. Медицинская справка 086/у (для меда, педа и некоторых технических).
6. Документы о льготах (БВИ, особая квота).
"""

FAQ_TEXT = """
❓ **ЧАСТЫЕ ВОПРОСЫ:**

1️⃣ **Сколько вузов?**
Можно подать в 5 вузов, выбрав до 5 направлений в каждом.

2️⃣ **Что такое Приоритет?**
Это ваш рейтинг желаний. Вуз зачислит вас на наивысший приоритет, куда вы проходите по баллам.

3️⃣ **Оригинал аттестата?**
Нужен до 3 августа (12:00 МСК) в вуз, куда вы хотите быть зачислены.

4️⃣ **Вторая волна?**
Нет! Зачисление проходит в одну волну.
"""

# --- ЗАГРУЗКА БАЗЫ ДАННЫХ ---
def load_universities():
    db = {'tech': [], 'human': [], 'med': []}
    if not os.path.exists(DB_FILE): return db
    try:
        with open(DB_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                if len(row) < 8: continue
                # cat;name;city;major;score_bud;score_paid;price;url
                cat = row[0].strip()
                try:
                    score_bud = int(row[4].strip())
                    score_paid = int(row[5].strip())
                    price = int(row[6].strip())
                except: continue
                
                url = row[7].strip()

                if cat in db:
                    db[cat].append({
                        'name': row[1].strip(), 'city': row[2].strip(), 
                        'major': row[3].strip(), 'budget': score_bud,
                        'paid': score_paid, 'price': price, 'url': url
                    })
    except Exception as e: print(f"Ошибка базы: {e}")
    return db

universities_db = load_universities()

# --- СИСТЕМА ПОДПИСОК ---
def add_subscription(user_id, subject):
    subs = []
    if os.path.exists(SUBS_FILE):
        with open(SUBS_FILE, 'r', encoding='utf-8') as f: subs = list(csv.reader(f))
    for row in subs:
        if str(row[0]) == str(user_id) and row[1] == subject: return False
    with open(SUBS_FILE, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([user_id, subject])
    return True

def notification_loop():
    while True:
        # Рассылка уведомлений в 09:00 утра
        if datetime.now().strftime("%H:%M") == "09:00":
            if os.path.exists(SUBS_FILE):
                with open(SUBS_FILE, 'r', encoding='utf-8') as f:
                    for row in csv.reader(f):
                        try:
                            user_id, subj = row[0], row[1]
                            if subj in EXAM_DATES:
                                days = (datetime.strptime(EXAM_DATES[subj], "%Y-%m-%d") - datetime.now()).days
                                if days > 0:
                                    bot.send_message(user_id, f"🔔 Напоминание!\nДо ЕГЭ ({subj}) осталось: **{days} дн.**", parse_mode="Markdown")
                        except: pass
            time.sleep(61)
        time.sleep(30)

t = threading.Thread(target=notification_loop)
t.daemon = True
t.start()

# --- СТАТИСТИКА ---
def save_to_csv(user_id, username, direction, city, score):
    try:
        exists = os.path.isfile(STATS_FILE)
        with open(STATS_FILE, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            if not exists: writer.writerow(['ID', 'Ник', 'Время', 'Направление', 'Город', 'Баллы'])
            uname = username if username else "Аноним"
            writer.writerow([user_id, uname, datetime.now().strftime("%Y-%m-%d %H:%M"), direction, city, score])
    except: pass

# =======================
# 🤖 ГЛАВНОЕ МЕНЮ
# =======================
@bot.message_handler(commands=['start'])
def start(message):
    global universities_db
    universities_db = load_universities()
    user_data[message.chat.id] = {'state': 'menu'}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Найти вуз", "🧠 Тест: Кто я?") 
    markup.row("🎯 По предметам", "📩 Обратная связь")
    markup.row("🏆 Доп. баллы", "📅 Даты", "📂 Документы")
    markup.row("📄 Памятка (PDF)", "⏳ Таймер", "❓ Частые вопросы")

    bot.send_message(message.chat.id, "👋 Привет! Я — навигатор абитуриента.\nВыбери действие:", reply_markup=markup)

# =======================
# 📢 АДМИН-РАССЫЛКА
# =======================
@bot.message_handler(commands=['sendall'])
def admin_broadcast(message):
    if message.from_user.id != ADMIN_ID: 
        bot.send_message(message.chat.id, "⛔ Вы не админ.")
        return
    text = message.text.replace('/sendall', '').strip()
    if not text:
        bot.send_message(message.chat.id, "Текст пустой. Пиши: /sendall Текст")
        return
    
    ids = set()
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader, None)
            for row in reader:
                if row: ids.add(row[0])
    
    count = 0
    for uid in ids:
        try:
            bot.send_message(uid, f"📢 **НОВОСТИ:**\n\n{text}", parse_mode="Markdown")
            count += 1
            time.sleep(0.1)
        except: pass
    bot.send_message(message.chat.id, f"✅ Отправлено: {count}")

# =======================
# 🧠 ТЕСТ ПРОФОРИЕНТАЦИИ
# =======================
@bot.message_handler(func=lambda m: m.text == "🧠 Тест: Кто я?")
def quiz_start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔧 Техника", callback_data="q1_tech"),
               types.InlineKeyboardButton("🗣 Люди", callback_data="q1_human"))
    markup.add(types.InlineKeyboardButton("🌿 Природа", callback_data="q1_bio"),
               types.InlineKeyboardButton("🎨 Творчество", callback_data="q1_art"))
    bot.send_message(message.chat.id, "🤖 **Вопрос 1:** С чем интереснее работать?", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('q1_'))
def quiz_q2(call):
    c = call.data.split('_')[1]
    mk = types.InlineKeyboardMarkup()
    if c == 'tech':
        mk.add(types.InlineKeyboardButton("💻 Код", callback_data="res_IT"), types.InlineKeyboardButton("⚙️ Механизмы", callback_data="res_ENG"))
    elif c == 'human':
        mk.add(types.InlineKeyboardButton("⚖️ Право", callback_data="res_LAW"), types.InlineKeyboardButton("🌍 Языки", callback_data="res_LING"))
    elif c == 'bio':
        mk.add(types.InlineKeyboardButton("🩺 Лечить", callback_data="res_MED"), types.InlineKeyboardButton("🔬 Изучать", callback_data="res_SCI"))
    elif c == 'art':
        mk.add(types.InlineKeyboardButton("🖌 Дизайн", callback_data="res_DES"), types.InlineKeyboardButton("🎭 Сцена", callback_data="res_ACT"))
    bot.edit_message_text("🤖 **Вопрос 2:** Что выберешь?", call.message.chat.id, call.message.message_id, reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data.startswith('res_'))
def quiz_res(call):
    r = call.data.split('_')[1]
    res_map = {'IT': 'IT и Программирование', 'ENG': 'Инженерия', 'LAW': 'Юриспруденция', 'LING': 'Лингвистика',
               'MED': 'Медицина', 'SCI': 'Наука (Био/Хим)', 'DES': 'Дизайн', 'ACT': 'Творчество'}
    bot.edit_message_text(f"🔮 Твой путь: **{res_map.get(r)}**.\n\nЖми 'Найти вуз' и ищи это направление!", 
                          call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# =======================
# 📩 ОБРАТНАЯ СВЯЗЬ
# =======================
@bot.message_handler(func=lambda m: m.text == "📩 Обратная связь")
def feedback_start(message):
    msg = bot.send_message(message.chat.id, "✍️ Напиши сообщение админу:")
    bot.register_next_step_handler(msg, feedback_send)

def feedback_send(message):
    if message.text:
        try:
            bot.send_message(ADMIN_ID, f"📩 **От @{message.from_user.username}:**\n{message.text}", parse_mode="Markdown")
            bot.send_message(message.chat.id, "✅ Отправлено!")
        except:
            bot.send_message(message.chat.id, "Ошибка отправки админу.")
    start(message)

# =======================
# ⏳ ТАЙМЕР И УВЕДОМЛЕНИЯ
# =======================
@bot.message_handler(func=lambda m: m.text == "⏳ Таймер")
def timer_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Русский язык", "Математика (Б/П)")
    markup.row("История/Лит/Хим", "Общество/Физика")
    markup.row("Био/Гео/Ин.яз", "Информатика (КЕГЭ)")
    markup.row("🔙 В меню")
    bot.send_message(message.chat.id, "⏰ Выбери предмет:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in EXAM_DATES.keys())
def show_timer(message):
    days = (datetime.strptime(EXAM_DATES[message.text], "%Y-%m-%d") - datetime.now()).days
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("🔔 Включить уведомления", callback_data=f"sub_{message.text}"))
    bot.send_message(message.chat.id, f"📅 **{message.text}**: {EXAM_DATES[message.text]}\n🔥 Осталось: **{days} дней**", parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data.startswith('sub_'))
def sub_handler(call):
    subj = call.data.split('sub_')[1]
    if add_subscription(call.message.chat.id, subj):
        bot.answer_callback_query(call.id, "✅ Подписка оформлена!")
        bot.send_message(call.message.chat.id, f"Я буду напоминать про **{subj}** каждое утро.")
    else: bot.answer_callback_query(call.id, "Уже подписан!")

# =======================
# 🔍 ПОИСК ВУЗОВ
# =======================
@bot.message_handler(func=lambda m: m.text == "🚀 Найти вуз")
def ask_dir(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Техническое 💻", "Гуманитарное ⚖️", "Медицина 🧬", "🔙 В меню")
    bot.send_message(message.chat.id, "Выбери профиль:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔙 В меню")
def back(message): start(message)

@bot.message_handler(func=lambda m: m.text in ["Техническое 💻", "Гуманитарное ⚖️", "Медицина 🧬"])
def ask_city(message):
    cat = "tech" if "Техническое" in message.text else "human" if "Гуманитарное" in message.text else "med"
    user_data[message.chat.id] = {'cat': cat, 'cat_name': message.text}
    bot.send_message(message.chat.id, "🏙 Город (например: Красноярск):", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: not m.text.isdigit() and m.chat.id in user_data and 'city' not in user_data[m.chat.id] and user_data[m.chat.id].get('state') != 'menu')
def check_city(message):
    raw = message.text.lower().strip()
    city_name = CITY_ALIASES.get(raw, raw)
    cat = user_data[message.chat.id]['cat']
    found = False
    for u in universities_db[cat]:
        if u['city'].lower() == city_name.lower():
            city_name = u['city']; found = True; break
    if found:
        user_data[message.chat.id]['city'] = city_name
        bot.send_message(message.chat.id, f"✅ Город **{city_name}** найден.\nВведи баллы ЕГЭ:", parse_mode="Markdown")
    else: bot.send_message(message.chat.id, "В этом городе нет таких вузов.")

@bot.message_handler(func=lambda m: m.text.isdigit())
def result(message):
    if message.chat.id not in user_data or 'city' not in user_data[message.chat.id]: start(message); return
    score = int(message.text)
    data = user_data[message.chat.id]
    save_to_csv(message.from_user.id, message.from_user.username, data['cat_name'], data['city'], score)
    
    unis = [u for u in universities_db[data['cat']] if u['city'] == data['city']]
    unis.sort(key=lambda x: x['budget'], reverse=True)
    
    passed, paid = [], []
    for u in unis:
        if score >= u['budget']: passed.append(u)
        elif score >= u['paid']: paid.append(u)
            
    txt = f"📊 **Результат для г. {data['city']} ({score} б.):**\n\n"
    if passed:
        txt += "✅ **ПРОХОДИШЬ НА БЮДЖЕТ:**\n"
        for u in passed: txt += f"🎓 **[{u['name']}]({u['url']})**\n   └ {u['major']}: от {u['budget']} б.\n"
    else: txt += "❌ На бюджет не хватает.\n"
    
    if paid:
        txt += "\n💰 **ПЛАТНОЕ / ЦЕЛЕВОЕ:**\n"
        for u in paid:
            price_fmt = "{:,}".format(u['price']).replace(',', ' ')
            txt += f"🔸 **[{u['name']}]({u['url']})** ({u['major']})\n   └ Цена: {price_fmt} ₽\n"
            
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚀 Найти вуз", "🔙 В меню")
    bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True)
    user_data.pop(message.chat.id, None)

# --- СПРАВОЧНИКИ ---
@bot.message_handler(func=lambda m: m.text == "🎯 По предметам")
def sub_menu(message):
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.row("🧮 Мат + ⚛️ Физ", "🧮 Мат + 💻 Инф")
    mk.row("🧬 Био + 🧪 Хим", "📚 Общ + 🇬🇧 Инг")
    mk.row("📚 Общ + 📜 Ист", "🔙 В меню")
    bot.send_message(message.chat.id, "Твой набор:", reply_markup=mk)

@bot.message_handler(func=lambda m: m.text in SUBJECTS_INFO.keys())
def show_prof(message): bot.send_message(message.chat.id, SUBJECTS_INFO[message.text], parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📂 Документы")
def show_doc(message): bot.send_message(message.chat.id, DOCUMENTS_LIST, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🏆 Доп. баллы")
def show_bon(message): bot.send_message(message.chat.id, "🏆 **БОНУСЫ:**\n🥇 Медаль: +5-10\n🏃 ГТО: +2-5\n🤝 Волонтерство: +1-2\n📝 Сочинение: до +10", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📅 Даты")
def show_cal(message): bot.send_message(message.chat.id, "📅 **2026:**\n🟢 20.06: Старт\n🟡 25.07: Стоп\n🟣 03.08: Приказы", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "❓ Частые вопросы")
def show_fq(message): bot.send_message(message.chat.id, FAQ_TEXT, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📄 Памятка (PDF)")
def send_pdf(message):
    if os.path.exists(PAMYATKA_FILE):
        with open(PAMYATKA_FILE, 'rb') as f: bot.send_document(message.chat.id, f, caption="🎁 Гайд.")
    else: bot.send_message(message.chat.id, "Файл не найден.")

try:
    print("Бот запущен...")
    bot.polling(none_stop=True)
except Exception as e:
    print(f"Ошибка: {e}")