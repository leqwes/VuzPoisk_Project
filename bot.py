import telebot
from telebot import types
import csv
import os
import time
import threading
from datetime import datetime

# ==========================================
# 👇 НАСТРОЙКИ 👇
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

# --- ТЕКСТОВЫЕ БЛОКИ ---

TEXT_SPO = """
🎓 **ПОСТУПЛЕНИЕ ПОСЛЕ КОЛЛЕДЖА (СПО)**

1️⃣ **ЕГЭ не обязательно!**
Выпускники колледжей имеют право сдавать **внутренние вступительные испытания** в вузе вместо ЕГЭ.
*Но! Некоторые топ-вузы требуют только ЕГЭ.*

2️⃣ **Что сдавать?**
Внутренние экзамены обычно профильные.
*Пример: вместо "Физики" будет "Электротехника".*

3️⃣ **Сроки:**
Прием документов для СПОшников часто заканчивается раньше (примерно 10-15 июля), так как вузу нужно время провести экзамены.

4️⃣ **Бонусы:**
Красный диплом колледжа может дать **+5-10 баллов** (зависит от вуза).
"""

TEXT_DOCS = """
📂 **ДОКУМЕНТЫ ДЛЯ ПОСТУПЛЕНИЯ:**

1. **Паспорт** (разворот + прописка).
2. **Аттестат/Диплом СПО** (с приложением!).
3. **СНИЛС** (Обязательно, по нему вас ищут в списках).
4. **Фото 3х4** (4-6 шт, матовые).
5. **Медицинская справка 086/у** (нужна на: Мед, Пед, Энергетику, Транспорт, Пищевое).
6. **Документы, подтверждающие льготы** (если есть).
"""

TEXT_BONUS = """
🏆 **ИНДИВИДУАЛЬНЫЕ ДОСТИЖЕНИЯ (+10 БАЛЛОВ):**

🥇 **Медаль «За особые успехи в учении»:**
• I степени (Золото): +5-10 баллов.
• II степени (Серебро): +3-5 баллов.

🏃 **Значок ГТО:**
• Дают баллы за любой значок (золото/серебро/бронза), если удостоверение выдано! (+2-5 баллов).

🤝 **Волонтерство:**
• Нужна книжка волонтера. Учитываются часы за последние 4 года (+1-2 балла).

📝 **Итоговое сочинение:**
• В ряде вузов (ВШЭ, МГУ) проверяют текст и могут накинуть до 10 баллов.
"""

TEXT_LGOTS = """
🌟 **ЛЬГОТЫ И КВОТЫ:**

1️⃣ **БВИ (Без вступительных испытаний):**
• Победители и призеры Всероса.
• Победители перечневых олимпиад (нужно подтвердить ЕГЭ на 75+ баллов).

2️⃣ **Особая квота (10% мест):**
• Дети-инвалиды, инвалиды I и II групп.
• Дети-сироты и оставшиеся без попечения родителей.

3️⃣ **Отдельная квота (10% мест):**
• Герои РФ.
• Участники СВО и их дети.
• Дети медработников, погибших от COVID-19 (на мед. специальности).

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

# --- СТАТИСТИКА (ВСЕХ ПОЛЬЗОВАТЕЛЕЙ) ---
def save_to_csv(user_id, username, action, info=""):
    try:
        exists = os.path.isfile(STATS_FILE)
        with open(STATS_FILE, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            if not exists: writer.writerow(['ID', 'Ник', 'Время', 'Действие', 'Инфо'])
            uname = username if username else "Аноним"
            writer.writerow([user_id, uname, datetime.now().strftime("%Y-%m-%d %H:%M"), action, info])
    except: pass

# --- ПОДПИСКИ (ВКЛ/ВЫКЛ) ---
def toggle_subscription(user_id, subject):
    subs = []
    if os.path.exists(SUBS_FILE):
        with open(SUBS_FILE, 'r', encoding='utf-8') as f: subs = list(csv.reader(f))
    
    new_subs = []
    found = False
    for row in subs:
        if len(row) < 2: continue
        # Если нашли совпадение - НЕ добавляем в новый список (удаляем)
        if str(row[0]) == str(user_id) and row[1] == subject:
            found = True
        else:
            new_subs.append(row)
    
    if not found:
        new_subs.append([user_id, subject]) # Добавляем, если не было
    
    with open(SUBS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(new_subs)
    
    return not found # True если включили, False если выключили

# --- ФОНОВЫЙ ТАЙМЕР ---
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

t = threading.Thread(target=notification_loop)
t.daemon = True
t.start()

# =======================
# 🤖 ГЛАВНОЕ МЕНЮ
# =======================
@bot.message_handler(commands=['start'])
def start(message):
    # СОХРАНЯЕМ ПОЛЬЗОВАТЕЛЯ СРАЗУ ПРИ СТАРТЕ
    save_to_csv(message.from_user.id, message.from_user.username, "START", "Зашел в бота")
    
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
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🧩 Решать логические задачи", callback_data="type_LOGIC"))
    markup.add(types.InlineKeyboardButton("🗣 Общаться и убеждать", callback_data="type_SOCIAL"))
    markup.add(types.InlineKeyboardButton("🎨 Создавать и творить", callback_data="type_CREATIVE"))
    markup.add(types.InlineKeyboardButton("🔬 Изучать природу/людей", callback_data="type_NATURE"))
    
    bot.send_message(message.chat.id, "🧐 **Вопрос 1 из 2:**\nЧто тебе нравится делать больше всего?", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('type_'))
def quiz_step2(call):
    t = call.data.split('_')[1]
    markup = types.InlineKeyboardMarkup()
    
    if t == 'LOGIC':
        markup.add(types.InlineKeyboardButton("💻 Код и алгоритмы", callback_data="res_IT"))
        markup.add(types.InlineKeyboardButton("🏗 Механизмы и чертежи", callback_data="res_ENG"))
        text = "🤖 Тебе ближе виртуальный мир или реальные машины?"
    elif t == 'SOCIAL':
        markup.add(types.InlineKeyboardButton("⚖️ Законы и права", callback_data="res_LAW"))
        markup.add(types.InlineKeyboardButton("💰 Деньги и управление", callback_data="res_MAN"))
        text = "🤖 Ты хочешь защищать справедливость или управлять бизнесом?"
    elif t == 'CREATIVE':
        markup.add(types.InlineKeyboardButton("🖌 Визуал и Дизайн", callback_data="res_DES"))
        markup.add(types.InlineKeyboardButton("🎭 Тексты и Сцена", callback_data="res_ART"))
        text = "🤖 Ты создаешь глазами или словом/действием?"
    elif t == 'NATURE':
        markup.add(types.InlineKeyboardButton("🩺 Лечить людей", callback_data="res_MED"))
        markup.add(types.InlineKeyboardButton("🌿 Изучать биологию/химию", callback_data="res_BIO"))
        text = "🤖 Практическая медицина или наука?"
        
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('res_'))
def quiz_final(call):
    r = call.data.split('_')[1]
    
    results = {
        'IT': ("💻 Архитектор цифровых миров", "Твое призвание — IT. Ты видишь структуру там, где другие видят хаос.\n🎓 **Вузы:** ИТМО, МИРЭА, ВШЭ."),
        'ENG': ("⚙️ Создатель будущего", "Ты — Инженер. Ты знаешь, как все устроено и как это починить.\n🎓 **Вузы:** Бауманка, Политех, Горный."),
        'LAW': ("⚖️ Голос справедливости", "Ты — Юрист или Политик. Умеешь убеждать и знаешь правила игры.\n🎓 **Вузы:** МГЮА, СПбГУ, СФУ."),
        'MAN': ("💼 Лидер изменений", "Ты — Менеджер или Предприниматель. Видишь возможности и ведешь людей за собой.\n🎓 **Вузы:** ВШЭ, РАНХиГС, Финансовый."),
        'DES': ("🎨 Визионер", "Ты — Дизайнер или Архитектор. Делаешь этот мир красивее и удобнее.\n🎓 **Вузы:** МГСУ, Школа Дизайна, КГАСУ."),
        'ART': ("🎭 Творец смыслов", "Ты — Журналист, Актер или Писатель. Влияешь на умы людей.\n🎓 **Вузы:** МГУ (Журфак), ГИТИС, Институты Культуры."),
        'MED': ("🩺 Хранитель жизни", "Ты — Врач. Самая благородная и ответственная профессия.\n🎓 **Вузы:** Сеченовский, Павлова, КрасГМУ."),
        'BIO': ("🔬 Исследователь тайн", "Ты — Ученый (Биотехнолог, Химик). Двигаешь прогресс вперед.\n🎓 **Вузы:** МГУ, РХТУ, Тимирязевка.")
    }
    
    title, desc = results.get(r, ("Студент", "Универсальный специалист"))
    
    bot.edit_message_text(f"🔮 **Твой архетип: {title}**\n\n{desc}\n\n👇 *Нажми 'Найти вуз' в меню, чтобы подобрать место учебы!*", 
                          call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# =======================
# 📜 ИНФО-РАЗДЕЛЫ
# =======================
@bot.message_handler(func=lambda m: m.text == "🎓 После СПО")
def show_spo(message):
    bot.send_message(message.chat.id, TEXT_SPO, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🌟 Льготы и Квоты")
def show_lgots(message):
    bot.send_message(message.chat.id, TEXT_LGOTS, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🏆 Доп. баллы")
def show_bonus(message):
    bot.send_message(message.chat.id, TEXT_BONUS, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📂 Документы")
def show_docs(message):
    bot.send_message(message.chat.id, TEXT_DOCS, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📄 Памятка (PDF)")
def send_pdf(message):
    save_to_csv(message.from_user.id, message.from_user.username, "DOWNLOAD", "Памятка")
    if os.path.exists(PAMYATKA_FILE):
        with open(PAMYATKA_FILE, 'rb') as f: bot.send_document(message.chat.id, f, caption="🎁 Твой гайд по выбору вуза.")
    else: bot.send_message(message.chat.id, "Файл обновляется...")

# =======================
# ⏳ ТАЙМЕР (ВКЛ/ВЫКЛ)
# =======================
@bot.message_handler(func=lambda m: m.text == "⏳ Таймер")
def timer_menu(message):
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
                    is_sub = True
                    break
    
    btn_text = "🔕 Выключить уведомления" if is_sub else "🔔 Включить уведомления"
    
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(btn_text, callback_data=f"toggle_{message.text}"))
    
    bot.send_message(message.chat.id, f"📅 {message.text}: {date_str}\n🔥 Осталось: **{days} дней**", parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_'))
def toggle_callback(call):
    subj = call.data.split('toggle_')[1]
    status = toggle_subscription(call.message.chat.id, subj)
    
    new_text = "🔕 Выключить уведомления" if status else "🔔 Включить уведомления"
    msg_text = f"✅ Уведомления для **{subj}** включены! (09:00)" if status else f"❌ Уведомления для **{subj}** выключены."
    
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(new_text, callback_data=f"toggle_{subj}"))
    
    bot.answer_callback_query(call.id, "Настройки изменены")
    bot.edit_message_text(f"📅 {subj}\n\n👉 {msg_text}", call.message.chat.id, call.message.message_id, reply_markup=mk, parse_mode="Markdown")

# =======================
# 📩 ОБРАТНАЯ СВЯЗЬ
# =======================
@bot.message_handler(func=lambda m: m.text == "📩 Обратная связь")
def feedback_start(message):
    msg = bot.send_message(message.chat.id, "✍️ Напиши вопрос или предложение админу:")
    bot.register_next_step_handler(msg, feedback_send)

def feedback_send(message):
    if message.text:
        try:
            bot.send_message(ADMIN_ID, f"📩 **От @{message.from_user.username}:**\n{message.text}", parse_mode="Markdown")
            bot.send_message(message.chat.id, "✅ Сообщение отправлено!")
        except: pass
    start(message)

# =======================
# 📢 АДМИНКА
# =======================
@bot.message_handler(commands=['sendall'])
def admin_send(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace('/sendall', '').strip()
    if not text: return
    
    ids = set()
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8-sig') as f:
            for row in csv.reader(f, delimiter=';'):
                if len(row) > 0 and row[0].isdigit(): ids.add(row[0])
    
    count = 0
    for uid in ids:
        try:
            bot.send_message(uid, f"📢 **НОВОСТИ:**\n\n{text}", parse_mode="Markdown")
            count += 1
            time.sleep(0.1)
        except: pass
    bot.send_message(message.chat.id, f"✅ Отправлено: {count}")

@bot.message_handler(commands=['stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        with open(STATS_FILE, 'rb') as f: bot.send_document(message.chat.id, f, caption="📊 База пользователей")
    except: bot.send_message(message.chat.id, "База пуста.")

# =======================
# 🚀 ПОИСК ВУЗОВ
# =======================
@bot.message_handler(func=lambda m: m.text == "🚀 Найти вуз")
def ask_dir(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Техническое 💻", "Гуманитарное ⚖️", "Медицина 🧬", "🔙 В меню")
    bot.send_message(message.chat.id, "Выбери профиль:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔙 В меню")
def back(message): start(message)

@bot.message_handler(func=lambda m: m.text == "🎯 По предметам")
def sub_menu(message):
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.row("🧮 Мат + ⚛️ Физ", "🧮 Мат + 💻 Инф")
    mk.row("🧬 Био + 🧪 Хим", "📚 Общ + 🇬🇧 Инг")
    mk.row("📚 Общ + 📜 Ист", "🔙 В меню")
    bot.send_message(message.chat.id, "Твой набор:", reply_markup=mk)

@bot.message_handler(func=lambda m: m.text in SUBJECTS_INFO.keys())
def show_prof(message): bot.send_message(message.chat.id, SUBJECTS_INFO[message.text], parse_mode="Markdown")

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

try:
    print("Бот запущен...")
    bot.polling(none_stop=True)
except Exception as e:
    print(f"Ошибка: {e}")