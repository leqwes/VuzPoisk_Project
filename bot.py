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

EXAM_DATES = {
    "История/Лит/Хим": "2026-06-01",
    "Русский язык": "2026-06-04",
    "Математика (Б/П)": "2026-06-08",
    "Общество/Физика": "2026-06-11",
    "Био/Гео/Ин.яз": "2026-06-15",
    "Информатика (КЕГЭ)": "2026-06-18"
}

SUBJECTS_INFO = {
    "🧮 Мат + ⚛️ Физ": "**ТЕХНАРЬ:** Строительство, Нефтегаз, Авиастроение, Энергетика",
    "🧮 Мат + 💻 Инф": "**IT:** Программирование, Безопасность, Аналитика, AI",
    "🧬 Био + 🧪 Хим": "**МЕДИЦИНА:** Лечебное дело, Стоматология, Фармация, Ветеринария",
    "📚 Общ + 🇬🇧 Инг": "**МЕНЕДЖМЕНТ:** Логистика, Управление, Реклама, Гостиничное дело",
    "📚 Общ + 📜 Ист": "**ГУМАНИТАРИЙ:** Юриспруденция, Политология, История, Педагогика"
}

TEXT_SPO = """
🎓 **ПОСТУПЛЕНИЕ ПОСЛЕ КОЛЛЕДЖА (СПО)**

1️⃣ **ЕГЭ не обязательно!**
Выпускники колледжей имеют право сдавать **внутренние вступительные испытания** в вузе вместо ЕГЭ.
*Но! Некоторые топ-вузы требуют только ЕГЭ.*

2️⃣ **Что сдавать?**
Внутренние экзамены обычно профильные.
*Пример: вместо "Физики" будет "Электротехника".*

3️⃣ **Сроки:**
Прием документов для СПОшников часто заканчивается раньше (примерно 10-15 июля).

4️⃣ **Бонусы:**
Красный диплом колледжа может дать **+5-10 баллов**.
"""

TEXT_DOCS = """
📂 **ДОКУМЕНТЫ ДЛЯ ПОСТУПЛЕНИЯ:**

1. **Паспорт** (разворот + прописка).
2. **Аттестат/Диплом СПО** (с приложением!).
3. **СНИЛС** (Обязательно).
4. **Фото 3х4** (4-6 шт, матовые).
5. **Медицинская справка 086/у** (нужна на: Мед, Пед, Энергетику, Транспорт).
6. **Документы о льготах** (если есть).
"""

TEXT_BONUS = """
🏆 **ИНДИВИДУАЛЬНЫЕ ДОСТИЖЕНИЯ (+10 БАЛЛОВ):**

🥇 **Медаль (Золото/Серебро):** +3-10 баллов.
🏃 **Значок ГТО:** Любой знак, если есть удостоверение (+2-5 баллов).
🤝 **Волонтерство:** Книжка волонтера (+1-2 балла).
📝 **Итоговое сочинение:** В ряде вузов (ВШЭ, МГУ) до +10 баллов.
"""

TEXT_LGOTS = """
🌟 **ЛЬГОТЫ И КВОТЫ:**

1️⃣ **БВИ (Без вступительных испытаний):** Победители олимпиад.
2️⃣ **Особая квота (10%):** Инвалиды, сироты.
3️⃣ **Отдельная квота (10%):** Участники СВО и их дети.

*Для зачисления по квоте нужен подтверждающий документ!*
"""

# --- ЗАГРУЗКА БАЗЫ ---
def load_universities():
    db = {'tech': [], 'human': [], 'med': []}
    if not os.path.exists(DB_FILE): return db
    try:
        with open(DB_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                if len(row) < 8: continue
                cat = row[0].strip()
                try:
                    score_bud = int(row[4].strip())
                    score_paid = int(row[5].strip())
                    price = int(row[6].strip())
                except: continue
                url = row[7].strip()
                if cat in db:
                    db[cat].append({'name': row[1].strip(), 'city': row[2].strip(), 'major': row[3].strip(), 
                                    'budget': score_bud, 'paid': score_paid, 'price': price, 'url': url})
    except: pass
    return db

universities_db = load_universities()

# --- СТАТИСТИКА ---
def save_to_csv(user_id, username, action, info=""):
    try:
        exists = os.path.isfile(STATS_FILE)
        with open(STATS_FILE, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            if not exists: writer.writerow(['ID', 'Ник', 'Время', 'Действие', 'Инфо'])
            uname = username if username else "Аноним"
            writer.writerow([user_id, uname, datetime.now().strftime("%Y-%m-%d %H:%M"), action, info])
    except: pass

# --- ПОДПИСКИ ---
def toggle_subscription(user_id, subject):
    subs = []
    if os.path.exists(SUBS_FILE):
        with open(SUBS_FILE, 'r', encoding='utf-8') as f: subs = list(csv.reader(f))
    
    new_subs = []
    found = False
    for row in subs:
        if len(row) < 2: continue
        if str(row[0]) == str(user_id) and row[1] == subject:
            found = True # Удаляем подписку
        else:
            new_subs.append(row)
    
    if not found: new_subs.append([user_id, subject]) # Добавляем подписку
    
    with open(SUBS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(new_subs)
    
    return not found # True = включено, False = выключено

# --- ФОНОВЫЕ ЗАДАЧИ ---
def notification_loop():
    while True:
        if datetime.now().strftime("%H:%M") == "09:00":
            if os.path.exists(SUBS_FILE):
                with open(SUBS_FILE, 'r', encoding='utf-8') as f:
                    for row in csv.reader(f):
                        try:
                            if row[1] in EXAM_DATES:
                                days = (datetime.strptime(EXAM_DATES[row[1]], "%Y-%m-%d") - datetime.now()).days
                                if days > 0:
                                    bot.send_message(row[0], f"🔔 Напоминание!\nДо ЕГЭ ({row[1]}) осталось: **{days} дн.**", parse_mode="Markdown")
                        except: pass
            time.sleep(61)
        time.sleep(30)

def backup_loop():
    while True:
        # 18000 секунд = 5 часов
        time.sleep(18000)
        try:
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, 'rb') as f:
                    bot.send_document(ADMIN_ID, f, caption="💾 Авто-бэкап базы (5 часов)", disable_notification=True)
        except: pass

t1 = threading.Thread(target=notification_loop)
t1.daemon = True
t1.start()

t2 = threading.Thread(target=backup_loop)
t2.daemon = True
t2.start()

# =======================
# 🤖 ГЛАВНОЕ МЕНЮ
# =======================
@bot.message_handler(commands=['start'])
def start(message):
    save_to_csv(message.from_user.id, message.from_user.username, "START", "Главное меню")
    
    global universities_db
    universities_db = load_universities()
    user_data[message.chat.id] = {'state': 'menu'}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Найти вуз", "🧠 Тест: Кто я?") 
    markup.row("🎯 По предметам", "🎓 После СПО")
    markup.row("🏆 Доп. баллы", "🌟 Льготы и Квоты")
    markup.row("📂 Документы", "📩 Обратная связь")
    markup.row("📄 Памятка (PDF)", "⏳ Таймер")

    bot.send_message(message.chat.id, "👋 Привет! Я — навигатор абитуриента 2026.\nЯ знаю всё про поступление!\n👇 Выбери раздел:", reply_markup=markup)

# =======================
# 🧠 ТЕСТ "КТО Я?"
# =======================
@bot.message_handler(func=lambda m: m.text == "🧠 Тест: Кто я?")
def quiz_start(message):
    save_to_csv(message.from_user.id, message.from_user.username, "QUIZ", "Начал тест")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🧩 Логика", callback_data="type_LOGIC"),
               types.InlineKeyboardButton("🗣 Общение", callback_data="type_SOCIAL"))
    markup.add(types.InlineKeyboardButton("🎨 Творчество", callback_data="type_CREATIVE"),
               types.InlineKeyboardButton("🔬 Природа", callback_data="type_NATURE"))
    
    bot.send_message(message.chat.id, "🧐 **Вопрос 1:** Что тебе ближе?", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('type_'))
def quiz_step2(call):
    t = call.data.split('_')[1]
    markup = types.InlineKeyboardMarkup()
    
    if t == 'LOGIC':
        markup.add(types.InlineKeyboardButton("💻 Код", callback_data="res_IT"), types.InlineKeyboardButton("🏗 Механизмы", callback_data="res_ENG"))
    elif t == 'SOCIAL':
        markup.add(types.InlineKeyboardButton("⚖️ Право", callback_data="res_LAW"), types.InlineKeyboardButton("💰 Управление", callback_data="res_MAN"))
    elif t == 'CREATIVE':
        markup.add(types.InlineKeyboardButton("🖌 Дизайн", callback_data="res_DES"), types.InlineKeyboardButton("🎭 Сцена", callback_data="res_ART"))
    elif t == 'NATURE':
        markup.add(types.InlineKeyboardButton("🩺 Врач", callback_data="res_MED"), types.InlineKeyboardButton("🌿 Ученый", callback_data="res_BIO"))
        
    bot.edit_message_text("🤖 **Вопрос 2:** Выбери направление:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('res_'))
def quiz_final(call):
    r = call.data.split('_')[1]
    results = {
        'IT': "💻 Твой путь — IT. Вузы: ИТМО, МИРЭА, ВШЭ.",
        'ENG': "⚙️ Твой путь — Инженерия. Вузы: Бауманка, Политех.",
        'LAW': "⚖️ Твой путь — Юриспруденция. Вузы: МГЮА, СПбГУ.",
        'MAN': "💼 Твой путь — Менеджмент. Вузы: ВШЭ, РАНХиГС.",
        'DES': "🎨 Твой путь — Дизайн. Вузы: Школа Дизайна, МАРХИ.",
        'ART': "🎭 Твой путь — Искусство. Вузы: ГИТИС, ВГИК.",
        'MED': "🩺 Твой путь — Медицина. Вузы: Сеченовский, Павлова.",
        'BIO': "🔬 Твой путь — Наука. Вузы: МГУ, РХТУ."
    }
    
    save_to_csv(call.message.chat.id, call.message.chat.username, "QUIZ_RES", r)
    bot.edit_message_text(f"🔮 **Результат:**\n\n{results.get(r)}\n\n👇 *Жми 'Найти вуз' в меню!*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# =======================
# ⏳ ТАЙМЕР (ВКЛ/ВЫКЛ)
# =======================
@bot.message_handler(func=lambda m: m.text == "⏳ Таймер")
def timer_menu(message):
    save_to_csv(message.from_user.id, message.from_user.username, "BUTTON", "Таймер")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Русский язык", "Математика (Б/П)")
    markup.row("История/Лит/Хим", "Общество/Физика")
    markup.row("Био/Гео/Ин.яз", "Информатика (КЕГЭ)")
    markup.row("🔙 В меню")
    bot.send_message(message.chat.id, "⏰ Выбери предмет для настройки уведомлений:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in EXAM_DATES.keys())
def show_timer(message):
    date_str = EXAM_DATES[message.text]
    days = (datetime.strptime(date_str, "%Y-%m-%d") - datetime.now()).days
    
    is_sub = False
    if os.path.exists(SUBS_FILE):
        with open(SUBS_FILE, 'r') as f:
            for row in csv.reader(f):
                if len(row) >= 2 and str(row[0]) == str(message.chat.id) and row[1] == message.text:
                    is_sub = True; break
    
    btn_text = "🔕 Выключить уведомления" if is_sub else "🔔 Включить уведомления"
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(btn_text, callback_data=f"toggle_{message.text}"))
    
    bot.send_message(message.chat.id, f"📅 {message.text}: {date_str}\n🔥 Осталось: **{days} дней**", parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_'))
def toggle_callback(call):
    subj = call.data.split('toggle_')[1]
    status = toggle_subscription(call.message.chat.id, subj)
    
    new_text = "🔕 Выключить уведомления" if status else "🔔 Включить уведомления"
    msg_text = f"✅ Уведомления для **{subj}** включены!" if status else f"❌ Уведомления для **{subj}** выключены."
    
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(new_text, callback_data=f"toggle_{subj}"))
    
    bot.answer_callback_query(call.id, "Готово")
    bot.edit_message_text(f"📅 {subj}\n\n👉 {msg_text}", call.message.chat.id, call.message.message_id, reply_markup=mk, parse_mode="Markdown")

# =======================
# ℹ️ ИНФО (ТЕПЕРЬ ВСЕ ЗАПИСЫВАЕТСЯ В БАЗУ)
# =======================
@bot.message_handler(func=lambda m: m.text == "🎓 После СПО")
def show_spo(message):
    save_to_csv(message.from_user.id, message.from_user.username, "BUTTON", "После СПО")
    bot.send_message(message.chat.id, TEXT_SPO, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🌟 Льготы и Квоты")
def show_lgots(message):
    save_to_csv(message.from_user.id, message.from_user.username, "BUTTON", "Льготы")
    bot.send_message(message.chat.id, TEXT_LGOTS, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🏆 Доп. баллы")
def show_bonus(message):
    save_to_csv(message.from_user.id, message.from_user.username, "BUTTON", "Доп. баллы")
    bot.send_message(message.chat.id, TEXT_BONUS, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📂 Документы")
def show_docs(message):
    save_to_csv(message.from_user.id, message.from_user.username, "BUTTON", "Документы")
    bot.send_message(message.chat.id, TEXT_DOCS, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📩 Обратная связь")
def feedback(message):
    save_to_csv(message.from_user.id, message.from_user.username, "BUTTON", "Обратная связь")
    msg = bot.send_message(message.chat.id, "✍️ Напиши сообщение админу:")
    bot.register_next_step_handler(msg, lambda m: bot.send_message(ADMIN_ID, f"📩 {m.from_user.username}: {m.text}"))

@bot.message_handler(func=lambda m: m.text == "📄 Памятка (PDF)")
def send_pdf(message):
    save_to_csv(message.from_user.id, message.from_user.username, "DOWNLOAD", "Памятка")
    if os.path.exists(PAMYATKA_FILE):
        with open(PAMYATKA_FILE, 'rb') as f: bot.send_document(message.chat.id, f)
    else: bot.send_message(message.chat.id, "Файл обновляется...")

# =======================
# 🚀 ПОИСК ВУЗОВ
# =======================
@bot.message_handler(func=lambda m: m.text == "🚀 Найти вуз")
def ask_dir(message):
    save_to_csv(message.from_user.id, message.from_user.username, "BUTTON", "Найти вуз")
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
    save_to_csv(message.from_user.id, message.from_user.username, f"SEARCH: {data['city']}", str(score))
    
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

# --- АДМИНКА ---
@bot.message_handler(commands=['sendall'])
def admin_send(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace('/sendall', '').strip()
    ids = set()
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8-sig') as f:
            for row in csv.reader(f, delimiter=';'):
                if len(row) > 0 and row[0].isdigit(): ids.add(row[0])
    for uid in ids:
        try: bot.send_message(uid, text)
        except: pass
    bot.send_message(message.chat.id, f"✅ Отправлено: {len(ids)}")

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        with open(STATS_FILE, 'rb') as f: bot.send_document(message.chat.id, f, caption="📊 База пользователей")
    except: bot.send_message(message.chat.id, "База пуста.")

@bot.message_handler(func=lambda m: m.text == "🎯 По предметам")
def sub_menu(message):
    save_to_csv(message.from_user.id, message.from_user.username, "BUTTON", "По предметам")
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.row("🧮 Мат + ⚛️ Физ", "🧮 Мат + 💻 Инф")
    mk.row("🧬 Био + 🧪 Хим", "📚 Общ + 🇬🇧 Инг")
    mk.row("📚 Общ + 📜 Ист", "🔙 В меню")
    bot.send_message(message.chat.id, "Твой набор:", reply_markup=mk)

@bot.message_handler(func=lambda m: m.text in SUBJECTS_INFO.keys())
def show_prof(message): bot.send_message(message.chat.id, SUBJECTS_INFO[message.text], parse_mode="Markdown")

try:
    print("Бот запущен...")
    bot.polling(none_stop=True)
except Exception as e:
    print(f"Ошибка: {e}")