import telebot
from telebot import types
import csv
import os
from datetime import datetime

# ==========================================
TOKEN = '8475081241:AAGRD7eLxKhyLnsu14fch9oq2LtZzVijbkE' 
# ==========================================
bot = telebot.TeleBot(TOKEN)
user_data = {}
STATS_FILE = 'statistics.csv'
DB_FILE = 'vuz_database.csv'
PAMYATKA_FILE = 'pamyatka.pdf'

CITY_ALIASES = {
    "питер": "Санкт-Петербург", "спб": "Санкт-Петербург",
    "мск": "Москва", "москва": "Москва",
    "екб": "Екатеринбург", "екат": "Екатеринбург",
    "нижний": "Нижний Новгород",
    "владик": "Владивосток",
    "крас": "Красноярск",
    "крск": "Красноярск"
}

# --- РАСПИСАНИЕ ЕГЭ 2026 (ПО ТВОИМ ДАННЫМ) ---
EXAM_DATES = {
    "История/Лит/Хим": "2026-06-01",
    "Русский язык": "2026-06-04",
    "Математика (Б/П)": "2026-06-08",
    "Общество/Физика": "2026-06-11",
    "Био/Гео/Ин.яз": "2026-06-15",
    "Информатика (КЕГЭ)": "2026-06-18" 
    # Информатика идет 18 и 19, считаем до первого дня
}

# --- СПРАВОЧНИКИ ---
SUBJECTS_INFO = {
    "🧮 Мат + ⚛️ Физ": "**ТЕХНАРЬ-КЛАССИКА:**\n• Строительство\n• Машиностроение\n• Нефтегазовое дело\n• Электроэнергетика\n• Авиастроение",
    "🧮 Мат + 💻 Инф": "**IT-СФЕРА:**\n• Программная инженерия\n• Информационная безопасность\n• Системный анализ\n• Бизнес-информатика",
    "🧬 Био + 🧪 Хим": "**МЕДИЦИНА:**\n• Лечебное дело / Педиатрия\n• Стоматология\n• Фармация\n• Ветеринария\n• Биотехнологии",
    "📚 Общ + 🇬🇧 Инг": "**МЕНЕДЖМЕНТ:**\n• Логистика\n• Управление персоналом\n• Реклама и PR\n• Гостиничное дело",
    "📚 Общ + 📜 Ист": "**ГУМАНИТАРИЙ:**\n• Юриспруденция\n• Политология\n• История\n• Социология"
}

DOCUMENTS_LIST = """
📂 **СПИСОК ДОКУМЕНТОВ:**
1. Паспорт (скан).
2. Аттестат с приложением.
3. СНИЛС.
4. Фото 3х4 (4-6 шт.).
5. Медсправка 086/у (для меда/педа).
6. Документы о льготах.
"""

FAQ_TEXT = """
❓ **ЧАСТЫЕ ВОПРОСЫ:**
1️⃣ **Сколько вузов?** 5 вузов, до 5 направлений.
2️⃣ **Приоритет?** Зачислят на высший по списку, куда проходишь.
3️⃣ **Оригинал?** До 3 августа (12:00 МСК) в вуз зачисления.
4️⃣ **Вторая волна?** Нет, только одна!
"""

# --- ЗАГРУЗКА БАЗЫ ---
def load_universities():
    db = {'tech': [], 'human': [], 'med': []}
    if not os.path.exists(DB_FILE): return db
    try:
        with open(DB_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                if len(row) < 5: continue
                cat = row[0].strip()
                try: score = int(row[4].strip())
                except: continue
                if cat in db:
                    db[cat].append({'name': row[1].strip(), 'city': row[2].strip(), 'major': row[3].strip(), 'score': score})
    except: pass
    return db

universities_db = load_universities()

# --- СОХРАНЕНИЕ СТАТИСТИКИ ---
def save_to_csv(user_id, username, direction, city, score):
    try:
        exists = os.path.isfile(STATS_FILE)
        with open(STATS_FILE, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            if not exists: writer.writerow(['ID', 'Ник', 'Время', 'Направление', 'Город', 'Баллы'])
            uname = username if username else "Аноним"
            t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([user_id, uname, t, direction, city, score])
    except: pass

# --- ГЛАВНОЕ МЕНЮ ---
@bot.message_handler(commands=['start'])
def start(message):
    global universities_db
    universities_db = load_universities()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Найти вуз") 
    markup.row("🎯 Куда с моими предметами?")
    markup.row("📂 Документы", "❓ Частые вопросы")
    markup.row("🏆 Доп. баллы", "📅 Даты и Сроки")
    markup.row("📄 Скачать памятку", "⏳ Таймер до ЕГЭ")

    bot.send_message(message.chat.id, 
                     "👋 Привет! Я твой навигатор поступления.\n"
                     "👇 Выбери нужный раздел:", reply_markup=markup)

# --- ОБРАБОТКА ТАЙМЕРА (ОБНОВЛЕНО) ---
@bot.message_handler(func=lambda m: m.text == "⏳ Таймер до ЕГЭ")
def timer_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Кнопки перегруппированы под новое расписание
    markup.row("Русский язык", "Математика (Б/П)")
    markup.row("История/Лит/Хим", "Общество/Физика")
    markup.row("Био/Гео/Ин.яз", "Информатика (КЕГЭ)")
    markup.row("🔙 В меню")
    
    bot.send_message(message.chat.id, "⏰ Выбери свой предмет (Расписание 2026):", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in EXAM_DATES.keys())
def show_timer(message):
    date_str = EXAM_DATES[message.text]
    exam_date = datetime.strptime(date_str, "%Y-%m-%d")
    now = datetime.now()
    delta = exam_date - now
    
    subject = message.text
    
    if delta.days > 0:
        bot.send_message(message.chat.id, 
                         f"📅 Экзамен: **{subject}**\n"
                         f"Дата: {date_str}\n\n"
                         f"🔥 Осталось: **{delta.days} дней** 🔥\n"
                         f"Удачи в подготовке!", 
                         parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"Экзамен **{subject}** уже прошел!", parse_mode="Markdown")

# --- ОБРАБОТКА ПРЕДМЕТОВ ---
@bot.message_handler(func=lambda m: m.text == "🎯 Куда с моими предметами?")
def subjects_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🧮 Мат + ⚛️ Физ", "🧮 Мат + 💻 Инф")
    markup.row("🧬 Био + 🧪 Хим", "📚 Общ + 🇬🇧 Инг")
    markup.row("📚 Общ + 📜 Ист", "🔙 В меню")
    bot.send_message(message.chat.id, "Выбери свою комбинацию ЕГЭ:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in SUBJECTS_INFO.keys())
def show_professions(message):
    bot.send_message(message.chat.id, SUBJECTS_INFO[message.text], parse_mode="Markdown")

# --- СПРАВОЧНЫЕ КНОПКИ ---
@bot.message_handler(func=lambda m: m.text == "📂 Документы")
def show_docs(message): bot.send_message(message.chat.id, DOCUMENTS_LIST, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "❓ Частые вопросы")
def show_faq(message): bot.send_message(message.chat.id, FAQ_TEXT, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🏆 Доп. баллы")
def show_bonus(message):
    text = "🏆 **ЗА ЧТО ДАЮТ ДОП. БАЛЛЫ?**\n🥇 Золотая медаль: +5-10 б.\n🏃 ГТО: +2-5 б.\n🤝 Волонтерство: +1-2 б.\n📝 Сочинение: до +10 б."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📅 Даты и Сроки")
def show_calendar(message):
    text = "📅 **ГРАФИК 2026 (Проект):**\n🟢 20 июня: Старт приема.\n🟡 25 июля: Конец приема.\n🔴 27 июля: Списки.\n🟣 3-9 августа: Приказы."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📄 Скачать памятку")
def send_pamphlet(message):
    if os.path.exists(PAMYATKA_FILE):
        with open(PAMYATKA_FILE, 'rb') as f: bot.send_document(message.chat.id, f, caption="🎁 Твой гайд (PDF).")
    else: bot.send_message(message.chat.id, "Файл загружается...")

# --- ПОИСК ВУЗА ---
@bot.message_handler(func=lambda m: m.text == "🚀 Найти вуз")
def ask_dir(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Техническое 💻", "Гуманитарное ⚖️", "Медицина 🧬")
    markup.add("🔙 В меню")
    bot.send_message(message.chat.id, "Выбери профиль:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔙 В меню")
def back_menu(message): start(message)

@bot.message_handler(func=lambda m: m.text in ["Техническое 💻", "Гуманитарное ⚖️", "Медицина 🧬"])
def ask_city(message):
    cat = "tech" if "Техническое" in message.text else "human" if "Гуманитарное" in message.text else "med"
    user_data[message.chat.id] = {'cat': cat, 'cat_name': message.text}
    bot.send_message(message.chat.id, "🏙 Введи город (например: Красноярск):", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: not m.text.isdigit() and m.chat.id in user_data and 'city' not in user_data[m.chat.id])
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
    else:
        bot.send_message(message.chat.id, "В этом городе нет вузов по такому профилю.")

@bot.message_handler(func=lambda m: m.text.isdigit())
def result(message):
    if message.chat.id not in user_data or 'city' not in user_data[message.chat.id]: start(message); return
    score = int(message.text)
    data = user_data[message.chat.id]
    save_to_csv(message.from_user.id, message.from_user.username, data['cat_name'], data['city'], score)
    
    unis = [u for u in universities_db[data['cat']] if u['city'] == data['city']]
    unis.sort(key=lambda x: x['score'], reverse=True)
    passed, dream = [], []
    for u in unis:
        if score >= u['score']: passed.append(u)
        else: dream.append(u)
            
    txt = f"📊 **Результат для г. {data['city']} ({score} б.):**\n\n"
    if passed:
        txt += "✅ **ПРОХОДИШЬ НА БЮДЖЕТ:**\n"
        for u in passed: txt += f"🎓 **{u['name']}**\n   └ {u['major']}: от {u['score']} б.\n"
    else: txt += "❌ На бюджет пока не хватает.\n"
    if dream:
        dream.sort(key=lambda x: x['score'])
        txt += "\n⚠️ **РИСКОВАННЫЕ ВАРИАНТЫ:**\n"
        for u in dream:
            diff = u['score'] - score
            txt += f"🔸 **{u['name']}** ({u['major']})\n   └ Не хватает: {diff} б.\n"
            
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚀 Найти вуз", "🔙 В меню")
    bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=markup)
    user_data.pop(message.chat.id, None)

try:
    print("Бот запущен (Режим 2026)...")
    bot.polling(none_stop=True)
except Exception as e:
    print(f"Ошибка: {e}")
