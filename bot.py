import telebot
from telebot import types
import csv
import os
from datetime import datetime

# ==========================================
# 👇 ВСТАВЬ СЮДА ТОКЕН ВНУТРИ КАВЫЧЕК 👇
TOKEN = '8475081241:AAGRD7eLxKhyLnsu14fch9oq2LtZzVijbkE' 
# ==========================================

bot = telebot.TeleBot(TOKEN)
user_data = {}
STATS_FILE = 'statistics.csv'
DB_FILE = 'vuz_database.csv'

# Синонимы городов для умного поиска
CITY_ALIASES = {
    "питер": "Санкт-Петербург", "спб": "Санкт-Петербург",
    "мск": "Москва", "москва": "Москва",
    "екб": "Екатеринбург", "екат": "Екатеринбург",
    "нижний": "Нижний Новгород",
    "владик": "Владивосток",
    "казань": "Казань",
    "нск": "Новосибирск"
}

# --- ЗАГРУЗКА БАЗЫ ДАННЫХ (5 КОЛОНОК) ---
def load_universities():
    db = {'tech': [], 'human': [], 'med': []}
    
    # Проверка наличия файла
    if not os.path.exists(DB_FILE):
        print("❌ Ошибка: Файл vuz_database.csv не найден!")
        return db
    
    try:
        with open(DB_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')
            
            # Пробуем прочитать файл построчно
            for row in reader:
                # Пропускаем пустые или короткие строки (нужно минимум 5 колонок)
                if len(row) < 5: continue
                
                # Читаем данные: cat;name;city;major;score
                cat = row[0].strip()   # Категория
                name = row[1].strip()  # Вуз
                city = row[2].strip()  # Город
                major = row[3].strip() # Специальность
                
                # Пробуем превратить балл в число
                try:
                    score = int(row[4].strip())
                except ValueError:
                    continue # Если балл не число, пропускаем строку

                if cat in db:
                    db[cat].append({
                        'name': name, 
                        'city': city, 
                        'major': major, 
                        'score': score
                    })
                    
        # Подсчет количества специальностей
        total = sum(len(v) for v in db.values())
        print(f"✅ База загружена. Записей: {total}")
        
    except Exception as e:
        print(f"❌ Ошибка чтения базы: {e}")
    return db

# Загружаем базу при старте программы
universities_db = load_universities()

# --- СОХРАНЕНИЕ СТАТИСТИКИ ---
def save_to_csv(user_id, username, direction, city, score):
    try:
        exists = os.path.isfile(STATS_FILE)
        with open(STATS_FILE, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            # Если файл новый - пишем заголовки
            if not exists:
                writer.writerow(['ID', 'Ник', 'Время', 'Направление', 'Город', 'Баллы'])
            
            uname = username if username else "Аноним"
            t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([user_id, uname, t, direction, city, score])
    except Exception as e:
        print(f"Ошибка записи статистики: {e}")

# --- КОМАНДА /START ---
@bot.message_handler(commands=['start'])
def start(message):
    global universities_db
    universities_db = load_universities() # Перезагрузка базы (на случай обновлений)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚀 Найти вуз"))
    
    # Считаем количество уникальных городов в базе
    unique_cities = set()
    for cat_list in universities_db.values():
        for u in cat_list:
            unique_cities.add(u['city'])
    
    count = len(unique_cities)
    
    # ВОТ ТУТ МЫ ДОБАВИЛИ ЭМОДЖИ И УБРАЛИ ЛИШНИЕ ЗВЕЗДОЧКИ
    bot.send_message(message.chat.id, 
                     f"👋 Привет! Это умный поиск вузов.\n"
                     f"В моей базе 🏙 *{count} городов* 🇷🇺 России.\n"
                     "Нажми кнопку, чтобы начать поиск.", 
                     parse_mode="Markdown", reply_markup=markup)

# --- ВЫБОР НАПРАВЛЕНИЯ ---
@bot.message_handler(func=lambda m: m.text == "🚀 Найти вуз")
def ask_dir(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Техническое 💻", "Гуманитарное ⚖️", "Медицина 🧬")
    bot.send_message(message.chat.id, "Выбери профиль:", reply_markup=markup)

# --- ВВОД ГОРОДА ---
@bot.message_handler(func=lambda m: m.text in ["Техническое 💻", "Гуманитарное ⚖️", "Медицина 🧬"])
def ask_city(message):
    # Определяем код категории
    if "Техническое" in message.text: cat = "tech"
    elif "Гуманитарное" in message.text: cat = "human"
    else: cat = "med"
    
    user_data[message.chat.id] = {'cat': cat, 'cat_name': message.text}
    
    bot.send_message(message.chat.id, 
                     "🏙 **Напиши город** (например: Москва, Томск, Казань):", 
                     parse_mode="Markdown",
                     reply_markup=types.ReplyKeyboardRemove())

# --- ПРОВЕРКА ГОРОДА ---
@bot.message_handler(func=lambda m: not m.text.isdigit() and m.chat.id in user_data and 'city' not in user_data[m.chat.id])
def check_city(message):
    raw = message.text.lower().strip()
    # Проверка синонимов (Питер -> Санкт-Петербург)
    city_name = CITY_ALIASES.get(raw, raw)
    cat = user_data[message.chat.id]['cat']
    
    # Ищем город в базе
    found_real_name = None
    for u in universities_db[cat]:
        if u['city'].lower() == city_name.lower():
            found_real_name = u['city']
            break
            
    if found_real_name:
        user_data[message.chat.id]['city'] = found_real_name
        bot.send_message(message.chat.id, 
                         f"✅ Город **{found_real_name}** найден.\nТеперь введи свои баллы ЕГЭ (сумма):", 
                         parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, 
                         f"В городе **{message.text}** нет специальностей по этому профилю в моей базе. Попробуй другой (например: Москва, Новосибирск).")

# --- ВЫВОД РЕЗУЛЬТАТА ---
@bot.message_handler(func=lambda m: m.text.isdigit())
def result(message):
    # Проверка, что пользователь прошел предыдущие шаги
    if message.chat.id not in user_data or 'city' not in user_data[message.chat.id]:
        bot.send_message(message.chat.id, "/start")
        return
    
    score = int(message.text)
    data = user_data[message.chat.id]
    
    # Сохраняем статистику
    save_to_csv(message.from_user.id, message.from_user.username, data['cat_name'], data['city'], score)
    
    # Фильтруем вузы: только нужная категория и нужный город
    unis = [u for u in universities_db[data['cat']] if u['city'] == data['city']]
    
    # Сортируем: сначала самые сложные (высокий балл)
    unis.sort(key=lambda x: x['score'], reverse=True)
    
    passed = [] # Куда проходим
    dream = []  # Куда не хватает
    
    for u in unis:
        if score >= u['score']:
            passed.append(u)
        else:
            dream.append(u)
            
    # ФОРМИРУЕМ СООБЩЕНИЕ
    txt = f"📊 **Специальности в г. {data['city']} ({score} б.):**\n\n"
    
    if passed:
        txt += "✅ **ВЫ ПРОХОДИТЕ НА БЮДЖЕТ:**\n"
        for u in passed:
            # Выводим: ВУЗ — Специальность: Балл
            txt += f"🎓 **{u['name']}**\n   └ {u['major']}: от {u['score']} б.\n"
    else:
        txt += "❌ На бюджет пока не хватает.\n"
        
    if dream:
        dream.sort(key=lambda x: x['score']) # Сортируем мечту от меньшего к большему
        txt += "\n🔒 **НЕ ХВАТАЕТ БАЛЛОВ (РИСКОВАННО):**\n"
        for u in dream:
            diff = u['score'] - score
            txt += f"🔸 **{u['name']}**\n   └ {u['major']}: {u['score']} (еще +{diff})\n"
            
    # Кнопка перезапуска
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚀 Найти вуз"))
    
    bot.send_message(message.chat.id, txt, parse_mode="Markdown", reply_markup=markup)
    
    # Очищаем данные пользователя
    user_data.pop(message.chat.id, None)

print("Бот запущен...")
try:
    bot.polling(none_stop=True)
except Exception as e:
    print(f"ОШИБКА: {e}")
    input("Нажми Enter чтобы выйти...")
