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
    "История": "2026-06-01", "Химия": "2026-06-01", "Литература": "2026-06-01",
    "Русский язык": "2026-06-04",
    "Математика": "2026-06-08", "Математика (Профиль)": "2026-06-08",
    "Обществознание": "2026-06-11", "Физика": "2026-06-11",
    "Биология": "2026-06-15", "Ин.яз": "2026-06-15",
    "Информатика": "2026-06-18"
}

SUBJECTS_INFO = {
    "🧮 Мат + ⚛️ Физ": "**ТЕХНАРЬ:**\n🔹 Строительство\n🔹 Нефтегазовое дело\n🔹 Авиастроение\n🔹 Электроэнергетика",
    "🧮 Мат + 💻 Инф": "**IT-СФЕРА:**\n🔹 Программная инженерия\n🔹 Информационная безопасность\n🔹 Аналитика данных",
    "🧬 Био + 🧪 Хим": "**МЕДИЦИНА:**\n🔹 Лечебное дело\n🔹 Стоматология\n🔹 Фармация\n🔹 Ветеринария",
    "📚 Общ + 🇬🇧 Инг": "**МЕНЕДЖМЕНТ:**\n🔹 Логистика\n🔹 Управление персоналом\n🔹 Реклама и PR",
    "📚 Общ + 📜 Ист": "**ГУМАНИТАРИЙ:**\n🔹 Юриспруденция\n🔹 Политология\n🔹 История\n🔹 Педагогика"
}

# --- КРАСИВЫЕ ТЕКСТОВЫЕ БЛОКИ ---

TEXT_SPO = """
🎓 **ПОСТУПЛЕНИЕ ПОСЛЕ СПО (КОЛЛЕДЖА)**
───────────────
Выпускники колледжей имеют особые права:

1️⃣ **Без ЕГЭ:** Вы можете сдавать внутренние вступительные экзамены в вузе.
2️⃣ **Бонусы:** Диплом с отличием часто дает **+5-10 баллов**.
3️⃣ **Сроки:** Прием документов обычно заканчивается раньше (10-15 июля).
"""

TEXT_LGOTS = """
🌟 **ЛЬГОТЫ И КВОТЫ**
───────────────
Кто поступает вне общего конкурса:

🔹 **БВИ (Без испытаний):** Победители Всероса и перечневых олимпиад (при подтверждении ЕГЭ 75+).
🔹 **Особая квота (10%):** Дети-инвалиды, сироты, ветераны боевых действий.
🔹 **Отдельная квота (10%):** Герои РФ, участники СВО и их дети.
"""

TEXT_BONUS = """
🏆 **КАК ПОЛУЧИТЬ +10 БАЛЛОВ?**
───────────────
Индивидуальные достижения решают всё!

🥇 **Медаль:** +5-10 баллов (Золото/Серебро).
🏃 **ГТО:** +2-5 баллов (Любой значок!).
🤝 **Волонтерство:** +1-2 балла (Книжка волонтера).
📝 **Итоговое сочинение:** до +10 баллов (ВШЭ, МГУ).
"""

TEXT_DOCS = """
📂 **СПИСОК ДОКУМЕНТОВ**
───────────────
Не забудь взять с собой:

✅ **Паспорт** (скан разворота и прописки).
✅ **Аттестат / Диплом** (с приложением!).
✅ **СНИЛС** (обязательно).
✅ **Фото 3х4** (матовые, 4-6 шт.).
✅ **Медсправка 086/у** (Мед, Пед, Энергетика).
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
            found = True
        else:
            new_subs.append(row)
    
    if not found: new_subs.append([user_id, subject])
    
    with open(SUBS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(new_subs)
    return not found

# --- ФОНОВЫЕ ПОТОКИ ---
def notification_loop():
    while True:
        if datetime.now().strftime("%H:%M") == "09:00":
            if os.path.exists(SUBS_FILE):
                with open(SUBS_FILE, 'r', encoding='utf-8') as f:
                    for row in csv.reader(f):
                        try:
                            for key, date_str in EXAM_DATES.items():
                                if key in row[1]:
                                    days = (datetime.strptime(date_str, "%Y-%m-%d") - datetime.now()).days
                                    if days > 0:
                                        bot.send_message(row[0], f"🔔 **Напоминание!**\nДо ЕГЭ ({row[1]}) осталось: **{days} дн.**", parse_mode="Markdown")
                                    break
                        except: pass
            time.sleep(61)
        time.sleep(30)

def backup_loop():
    while True:
        time.sleep(18000) # 5 часов
        try:
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, 'rb') as f:
                    bot.send_document(ADMIN_ID, f, caption="💾 Авто-отчет базы", disable_notification=True)
        except: pass

t1 = threading.Thread(target=notification_loop)
t1.daemon = True
t1.start()

t2 = threading.Thread(target=backup_loop)
t2.daemon = True
t2.start()

# =======================
# 🤖 ГЛАВНОЕ МЕНЮ (СЕТКА)
# =======================
@bot.message_handler(commands=['start'])
def start(message):
    save_to_csv(message.from_user.id, message.from_user.username, "START", "Меню")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    # 1 РЯД: Главное
    markup.row("🚀 Найти вуз", "🧠 Тест: Кто я?") 
    # 2 РЯД: Инструменты
    markup.row("🎯 По предметам", "⏳ Таймер")
    # 3 РЯД: Справочник
    markup.row("🎓 После СПО", "🌟 Льготы и Квоты")
    markup.row("🏆 Доп. баллы", "📂 Документы")
    # 4 РЯД: Сервис
    markup.row("📄 Памятка", "📩 Обратная связь")

    welcome_text = (
        f"👋 **Привет, {message.from_user.first_name}!**\n\n"
        "Я — твой навигатор по поступлению в 2026 году.\n"
        "Здесь нет воды, только факты, цифры и польза.\n\n"
        "👇 **Выбери, с чего начнем:**"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

# =======================
# 🚀 ПОИСК ВУЗОВ (ПОШАГОВЫЙ)
# =======================
@bot.message_handler(func=lambda m: m.text == "🚀 Найти вуз")
def step1_cat(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Техническое 💻", "Гуманитарное ⚖️")
    markup.row("Медицина 🧬", "🔙 В меню")
    bot.send_message(message.chat.id, "1️⃣ Выбери направление:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Техническое 💻", "Гуманитарное ⚖️", "Медицина 🧬"])
def step2_city(message):
    cat = "tech" if "Техническое" in message.text else "human" if "Гуманитарное" in message.text else "med"
    user_data[message.chat.id] = {'cat': cat}
    bot.send_message(message.chat.id, "2️⃣ Напиши город (например: Красноярск):", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, step3_score)

def step3_score(message):
    if message.text == "/start": start(message); return
    if message.text == "🔙 В меню": start(message); return
    
    raw_city = message.text.lower().strip()
    city = CITY_ALIASES.get(raw_city, raw_city)
    
    cat = user_data[message.chat.id].get('cat', 'tech')
    found = False
    for u in universities_db[cat]:
        if u['city'].lower() == city.lower():
            city = u['city']
            found = True
            break
            
    if not found:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("🚀 Найти вуз", "🔙 В меню")
        bot.send_message(message.chat.id, "😔 В этом городе нет вузов по выбранному профилю.\nПопробуй другой город.", reply_markup=markup)
        return

    user_data[message.chat.id]['city'] = city
    bot.send_message(message.chat.id, f"✅ Город **{city}** найден.\n3️⃣ Введи сумму баллов ЕГЭ (3 предмета):", parse_mode="Markdown")
    bot.register_next_step_handler(message, step4_result)

def step4_result(message):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "⚠️ Нужно ввести число!")
        return
        
    score = int(message.text)
    data = user_data[message.chat.id]
    save_to_csv(message.from_user.id, message.from_user.username, "SEARCH", f"{data['city']} {score}")
    
    unis = [u for u in universities_db[data['cat']] if u['city'] == data['city']]
    unis.sort(key=lambda x: x['budget'], reverse=True)
    
    passed, paid = [], []
    for u in unis:
        if score >= u['budget']: passed.append(u)
        elif score >= u['paid']: paid.append(u)
            
    txt = f"📊 **Результат для г. {data['city']} ({score} б.):**\n"
    
    if passed:
        txt += "\n✅ **БЮДЖЕТ:**\n"
        for u in passed: txt += f"🎓 **[{u['name']}]({u['url']})**\n   └ {u['major']}: от {u['budget']} б.\n"
    else: txt += "\n❌ На бюджет не хватает.\n"
    
    if paid:
        txt += "\n💰 **ПЛАТНОЕ:**\n"
        for u in paid:
            price_fmt = "{:,}".format(u['price']).replace(',', ' ')
            txt += f"🔸 **[{u['name']}]({u['url']})** ({u['major']})\n   └ Цена: {price_fmt} ₽\n"

    txt += "\n_Данные за 2024/2025 год_" # ПОДПИСЬ

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Найти вуз", "🔙 В меню")
    # disable_web_page_preview=True чтобы не было картинок ссылок
    bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True)

# =======================
# 🧠 ТЕСТ
# =======================
@bot.message_handler(func=lambda m: m.text == "🧠 Тест: Кто я?")
def quiz_start(message):
    save_to_csv(message.from_user.id, message.from_user.username, "QUIZ", "Начал тест")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🧩 Логика", callback_data="q1_tech"),
               types.InlineKeyboardButton("🗣 Общение", callback_data="q1_human"))
    markup.add(types.InlineKeyboardButton("🎨 Творчество", callback_data="q1_art"),
               types.InlineKeyboardButton("🔬 Природа", callback_data="q1_bio"))
    bot.send_message(message.chat.id, "🧐 **Вопрос 1:** Что тебе ближе?", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('q1_'))
def quiz_q2(call):
    t = call.data.split('_')[1]
    mk = types.InlineKeyboardMarkup()
    if t == 'tech': mk.add(types.InlineKeyboardButton("💻 Код", callback_data="res_IT"), types.InlineKeyboardButton("⚙️ Механизмы", callback_data="res_ENG"))
    elif t == 'human': mk.add(types.InlineKeyboardButton("⚖️ Право", callback_data="res_LAW"), types.InlineKeyboardButton("💰 Бизнес", callback_data="res_MAN"))
    elif t == 'bio': mk.add(types.InlineKeyboardButton("🩺 Врач", callback_data="res_MED"), types.InlineKeyboardButton("🔬 Ученый", callback_data="res_SCI"))
    elif t == 'art': mk.add(types.InlineKeyboardButton("🖌 Дизайн", callback_data="res_DES"), types.InlineKeyboardButton("🎭 Сцена", callback_data="res_ART"))
    bot.edit_message_text("🤖 **Вопрос 2:** Выбери направление:", call.message.chat.id, call.message.message_id, reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data.startswith('res_'))
def quiz_res(call):
    r = call.data.split('_')[1]
    res_map = {'IT':'IT', 'ENG':'Инженерия', 'LAW':'Юриспруденция', 'MAN':'Менеджмент', 'MED':'Медицина', 'SCI':'Наука', 'DES':'Дизайн', 'ART':'Искусство'}
    bot.edit_message_text(f"🔮 Твой путь: **{res_map.get(r)}**.\n\nЖми '🚀 Найти вуз' в меню!", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# =======================
# ⏳ ТАЙМЕР
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
                    is_sub = True; break
    
    btn_text = "🔕 Выключить" if is_sub else "🔔 Включить уведомления"
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(btn_text, callback_data=f"toggle_{message.text}"))
    
    bot.send_message(message.chat.id, f"📅 {message.text}\n🔥 Осталось: **{days} дней**", parse_mode="Markdown", reply_markup=mk)

@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_'))
def toggle_callback(call):
    subj = call.data.split('toggle_')[1]
    status = toggle_subscription(call.message.chat.id, subj)
    new_text = "🔕 Выключить" if status else "🔔 Включить уведомления"
    msg = "✅ Включено!" if status else "❌ Выключено."
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(new_text, callback_data=f"toggle_{subj}"))
    bot.edit_message_text(f"📅 {subj}\n\n👉 {msg}", call.message.chat.id, call.message.message_id, reply_markup=mk)

# =======================
# ℹ️ ИНФО И АДМИНКА
# =======================
@bot.message_handler(func=lambda m: m.text == "🎯 По предметам")
def sub_menu(message):
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.row("🧮 Мат + ⚛️ Физ", "🧮 Мат + 💻 Инф")
    mk.row("🧬 Био + 🧪 Хим", "📚 Общ + 🇬🇧 Инг")
    mk.row("📚 Общ + 📜 Ист", "🔙 В меню")
    bot.send_message(message.chat.id, "Твой набор:", reply_markup=mk)

@bot.message_handler(func=lambda m: m.text in SUBJECTS_INFO.keys())
def show_prof(message): bot.send_message(message.chat.id, SUBJECTS_INFO[message.text], parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🔙 В меню")
def back(message): start(message)

@bot.message_handler(func=lambda m: m.text == "🎓 После СПО")
def info_spo(m): bot.send_message(m.chat.id, TEXT_SPO, parse_mode="Markdown")
@bot.message_handler(func=lambda m: m.text == "🌟 Льготы и Квоты")
def info_lgots(m): bot.send_message(m.chat.id, TEXT_LGOTS, parse_mode="Markdown")
@bot.message_handler(func=lambda m: m.text == "🏆 Доп. баллы")
def info_bonus(m): bot.send_message(m.chat.id, TEXT_BONUS, parse_mode="Markdown")
@bot.message_handler(func=lambda m: m.text == "📂 Документы")
def info_docs(m): bot.send_message(m.chat.id, TEXT_DOCS, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📄 Памятка")
def send_pdf(m):
    save_to_csv(m.from_user.id, m.from_user.username, "DOWNLOAD", "Памятка")
    if os.path.exists(PAMYATKA_FILE):
        with open(PAMYATKA_FILE, 'rb') as f: bot.send_document(m.chat.id, f)
    else: bot.send_message(m.chat.id, "Файл не найден.")

@bot.message_handler(func=lambda m: m.text == "📩 Обратная связь")
def feedback(m):
    msg = bot.send_message(m.chat.id, "✍️ Напиши сообщение:")
    bot.register_next_step_handler(msg, lambda mm: bot.send_message(ADMIN_ID, f"📩 {mm.from_user.username}: {mm.text}"))

@bot.message_handler(commands=['sendall'])
def admin_send(m):
    if m.from_user.id != ADMIN_ID: return
    txt = m.text.replace('/sendall', '').strip()
    ids = set()
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8-sig') as f:
            for r in csv.reader(f, delimiter=';'): 
                if len(r)>0 and r[0].isdigit(): ids.add(r[0])
    for uid in ids: 
        try: bot.send_message(uid, txt)
        except: pass
    bot.send_message(m.chat.id, f"✅ Отправлено: {len(ids)}")

@bot.message_handler(commands=['stats'])
def admin_stats(m):
    if m.from_user.id != ADMIN_ID: return
    try: 
        with open(STATS_FILE, 'rb') as f: bot.send_document(m.chat.id, f)
    except: pass

try:
    print("Бот запущен...")
    bot.polling(none_stop=True)
except Exception as e:
    print(f"Ошибка: {e}")