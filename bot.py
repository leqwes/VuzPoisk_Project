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

# --- РАСПИСАНИЕ ЕГЭ 2026 ---
EXAM_DATES = {
    "История/Лит/Хим": "2026-06-01",
    "Русский язык": "2026-06-04",
    "Математика (Б/П)": "2026-06-08",
    "Общество/Физика": "2026-06-11",
    "Био/Гео/Ин.яз": "2026-06-15",
    "Информатика (КЕГЭ)": "2026-06-18"
}

SUBJECTS_INFO = {
    "🧮 Мат + ⚛️ Физ": "**ТЕХНАРЬ-КЛАССИКА:**\n• Строительство\n• Машиностроение\n• Нефтегазовое дело\n• Электроэнергетика",
    "🧮 Мат + 💻 Инф": "**IT-СФЕРА:**\n• Программная инженерия\n• Информационная безопасность\n• Системный анализ",
    "🧬 Био + 🧪 Хим": "**МЕДИЦИНА:**\n• Лечебное дело\n• Стоматология\n• Фармация\n• Ветеринария",
    "📚 Общ + 🇬🇧 Инг": "**МЕНЕДЖМЕНТ:**\n• Логистика\n• Управление персоналом\n• Реклама и PR",
    "📚 Общ + 📜 Ист": "**ГУМАНИТАРИЙ:**\n• Юриспруденция\n• Политология\n• История"
}

DOCUMENTS_LIST = "📂 **СПИСОК ДОКУМЕНТОВ:**\n1. Паспорт\n2. Аттестат\n3. СНИЛС\n4. Фото 3х4\n5. Медсправка 086/у"
FAQ_TEXT = "❓ **ЧАСТЫЕ ВОПРОСЫ:**\n1️⃣ 5 вузов, 5 направлений.\n2️⃣ Зачисление по высшему приоритету.\n3️⃣ Оригинал до 3 августа.\n4️⃣ Одна волна зачисления."

# --- ЗАГРУЗКА БАЗЫ (8 КОЛОНОК) ---
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
                    score_budget = int(row[4].strip())
                    score_paid = int(row[5].strip())
                    price = int(row[6].strip())
                except: continue
                
                if cat in db:
                    db[cat].append({
                        'name': row[1].strip(), 
                        'city': row[2].strip(), 
                        'major': row[3].strip(), 
                        'budget': score_budget,
                        'paid': score_paid,
                        'price': price,
                        'url': row[7].strip()
                    })
    except Exception as e: print(f"Error: {e}")
    return db

universities_db = load_universities()

def save_to_csv(user_id, username, direction, city, score):
    try:
        exists = os.path.isfile(STATS_FILE)
        with open(STATS_FILE, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            if not exists: writer.writerow(['ID', 'Ник', 'Время', 'Направление', 'Город', 'Баллы'])
            writer.writerow([user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M"), direction, city, score])
    except: pass

@bot.message_handler(commands=['start'])
def start(message):
    global universities_db
    universities_db = load_universities()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 Найти вуз", "🎯 Куда с моими предметами?") 
    markup.row("📂 Документы", "❓ Частые вопросы")
    markup.row("🏆 Доп. баллы", "📅 Даты и Сроки")
    markup.row("📄 Скачать памятку", "⏳ Таймер до ЕГЭ")
    bot.send_message(message.chat.id, "👋 Привет! Я навигатор поступления.\nЯ знаю бюджетные и платные места.\n👇 Выбери раздел:", reply_markup=markup)

# --- ТАЙМЕР ---
@bot.message_handler(func=lambda m: m.text == "⏳ Таймер до ЕГЭ")
def timer_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Русский язык", "Математика (Б/П)")
    markup.row("История/Лит/Хим", "Общество/Физика")
    markup.row("Био/Гео/Ин.яз", "Информатика (КЕГЭ)")
    markup.row("🔙 В меню")
    bot.send_message(message.chat.id, "⏰ Выбери предмет (2026):", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in EXAM_DATES.keys())
def show_timer(message):
    date_str = EXAM_DATES[message.text]
    days = (datetime.strptime(date_str, "%Y-%m-%d") - datetime.now()).days
    msg = f"📅 **{message.text}**: {date_str}\n🔥 Осталось: **{days} дней**" if days > 0 else "Экзамен прошел!"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# --- ОБРАБОТЧИКИ ---
@bot.message_handler(func=lambda m: m.text == "🎯 Куда с моими предметами?")
def subjects_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🧮 Мат + ⚛️ Физ", "🧮 Мат + 💻 Инф")
    markup.row("🧬 Био + 🧪 Хим", "📚 Общ + 🇬🇧 Инг")
    markup.row("📚 Общ + 📜 Ист", "🔙 В меню")
    bot.send_message(message.chat.id, "Выбери комбинацию:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in SUBJECTS_INFO.keys())
def show_professions(message): bot.send_message(message.chat.id, SUBJECTS_INFO[message.text], parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📂 Документы")
def show_docs(message): bot.send_message(message.chat.id, DOCUMENTS_LIST, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "❓ Частые вопросы")
def show_faq(message): bot.send_message(message.chat.id, FAQ_TEXT, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🏆 Доп. баллы")
def show_bonus(message): bot.send_message(message.chat.id, "🏆 **БОНУСЫ:**\n🥇 Медаль: +5-10 б.\n🏃 ГТО: +2-5 б.\n🤝 Волонтерство: +1-2 б.\n📝 Сочинение: до +10 б.", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📅 Даты и Сроки")
def show_calendar(message): bot.send_message(message.chat.id, "📅 **2026:**\n🟢 20 июня: Старт\n🟡 25 июля: Конец приема\n🟣 3-9 августа: Приказы", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📄 Скачать памятку")
def send_pamphlet(message):
    if os.path.exists(PAMYATKA_FILE):
        with open(PAMYATKA_FILE, 'rb') as f: bot.send_document(message.chat.id, f, caption="🎁 Твой гайд (PDF).")
    else: bot.send_message(message.chat.id, "Файл загружается...")

# --- ПОИСК ---
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
    else: bot.send_message(message.chat.id, "В этом городе нет таких вузов.")

@bot.message_handler(func=lambda m: m.text.isdigit())
def result(message):
    if message.chat.id not in user_data or 'city' not in user_data[message.chat.id]: start(message); return
    score = int(message.text)
    data = user_data[message.chat.id]
    save_to_csv(message.from_user.id, message.from_user.username, data['cat_name'], data['city'], score)
    
    unis = [u for u in universities_db[data['cat']] if u['city'] == data['city']]
    unis.sort(key=lambda x: x['budget'], reverse=True) # Сортируем по бюджетному баллу
    
    passed_budget = []
    passed_paid = []
    
    for u in unis:
        if score >= u['budget']:
            passed_budget.append(u)
        elif score >= u['paid']:
            passed_paid.append(u)
            
    txt = f"📊 **Результат для г. {data['city']} ({score} б.):**\n\n"
    
    if passed_budget:
        txt += "✅ **ПРОХОДИШЬ НА БЮДЖЕТ:**\n"
        for u in passed_budget:
            txt += f"🎓 **[{u['name']}]({u['url']})**\n   └ {u['major']}: от {u['budget']} б.\n"
    else:
        txt += "❌ На бюджет баллов пока не хватает.\n"
        
    if passed_paid:
        txt += "\n💰 **ПРОХОДИШЬ НА ПЛАТНОЕ:**\n"
        for u in passed_paid:
            price_fmt = "{:,}".format(u['price']).replace(',', ' ')
            diff = u['budget'] - score
            txt += f"🔸 **[{u['name']}]({u['url']})**\n   └ {u['major']}: {u['paid']} б.\n   └ До бюджета: не хватило {diff} б.\n   └ Цена: **{price_fmt} ₽/год**\n"
    elif not passed_budget:
        txt += "\n😔 На платное тоже пока не хватает баллов."
            
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚀 Найти вуз", "🔙 В меню")
    bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True)
    user_data.pop(message.chat.id, None)

try:
    print("Бот запущен...")
    bot.polling(none_stop=True)
except Exception as e:
    print(f"Ошибка: {e}")