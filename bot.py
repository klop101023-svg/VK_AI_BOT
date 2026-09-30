import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import config
import requests
import json
import os
import time
from datetime import datetime, timedelta
import openai
from flask import Flask
import threading
from ddgs import DDGS

# === ПОДКЛЮЧЕНИЕ К ВК ===
vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

# === ПОДКЛЮЧЕНИЕ К AITUNNEL ===
client = openai.OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL,
)

# === ПУТИ К ФАЙЛАМ (постоянная папка BotHost) ===
DATA_DIR = os.environ.get("DATA_DIR", ".")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

ADMIN_ID = 1027228715

# === ПАМЯТЬ ДИАЛОГОВ ===
DIALOG_HISTORY = {}
MAX_HISTORY = 10
HISTORY_TTL_HOURS = 24

def load_history():
    global DIALOG_HISTORY
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                DIALOG_HISTORY = json.load(f)
            print(f"✅ История загружена: {len(DIALOG_HISTORY)} пользователей")
        except Exception as e:
            print(f"❌ Ошибка загрузки истории: {e}")
            DIALOG_HISTORY = {}

def save_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(DIALOG_HISTORY, f, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Ошибка сохранения истории: {e}")

def cleanup_old_history():
    now = datetime.now()
    to_delete = []
    for uid, data in DIALOG_HISTORY.items():
        try:
            last = datetime.strptime(data["last_active"], "%Y-%m-%d %H:%M:%S")
            if (now - last) > timedelta(hours=HISTORY_TTL_HOURS):
                to_delete.append(uid)
        except:
            to_delete.append(uid)
    for uid in to_delete:
        del DIALOG_HISTORY[uid]
    if to_delete:
        save_history()
        print(f"🧹 Очищено старых историй: {len(to_delete)}")

def get_history(user_id):
    uid = str(user_id)
    data = DIALOG_HISTORY.get(uid)
    if not data:
        return []
    try:
        last = datetime.strptime(data["last_active"], "%Y-%m-%d %H:%M:%S")
        if (datetime.now() - last) > timedelta(hours=HISTORY_TTL_HOURS):
            del DIALOG_HISTORY[uid]
            save_history()
            return []
    except:
        return []
    return data.get("messages", [])

def add_to_history(user_id, role, content):
    uid = str(user_id)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if uid not in DIALOG_HISTORY:
        DIALOG_HISTORY[uid] = {"messages": [], "last_active": now_str}
    DIALOG_HISTORY[uid]["messages"].append({"role": role, "content": content})
    DIALOG_HISTORY[uid]["last_active"] = now_str
    if len(DIALOG_HISTORY[uid]["messages"]) > MAX_HISTORY * 2:
        DIALOG_HISTORY[uid]["messages"] = DIALOG_HISTORY[uid]["messages"][-MAX_HISTORY * 2:]
    save_history()

def clear_history(user_id):
    uid = str(user_id)
    if uid in DIALOG_HISTORY:
        del DIALOG_HISTORY[uid]
        save_history()

# === МИНИ-СЕРВЕР ДЛЯ BOTHOST ===
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# === СТАТИСТИКА ===
def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_stats(stats):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Ошибка сохранения статистики: {e}")

def update_stats(user_id):
    stats = load_stats()
    user_id_str = str(user_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if user_id_str not in stats:
        stats[user_id_str] = {"first_seen": now, "last_seen": now, "messages": 0}
    else:
        stats[user_id_str]["last_seen"] = now
    stats[user_id_str]["messages"] += 1
    save_stats(stats)

# === КЛАВИАТУРА ===
def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("🌿 Главная", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("📋 Команды", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📊 Статистика", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("🧹 Очистить", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("📜 Правила", color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()

def send_message(user_id, text, keyboard=None, retries=2):
    """Отправляет сообщение с 2 повторными попытками."""
    for attempt in range(retries + 1):
        try:
            vk.messages.send(
                user_id=user_id,
                message=text,
                keyboard=keyboard if keyboard else get_main_keyboard(),
                random_id=get_random_id()
            )
            print(f"✅ Отправлено: {text[:50]}")
            return True
        except Exception as e:
            if attempt < retries:
                print(f"⚠️ Попытка {attempt + 1}/{retries + 1} не удалась: {e}")
                time.sleep(1)
            else:
                error_msg = f"Не удалось отправить после {retries + 1} попыток: {e}"
                print(f"❌ {error_msg}")
                notify_admin(error_msg, "send")
                return False

# === УВЕДОМЛЕНИЯ АДМИНУ ===
LAST_NOTIFY = {}

def notify_admin(error_text, error_type="general"):
    now = time.time()
    last = LAST_NOTIFY.get(error_type, 0)
    if now - last < 300:
        print(f"⏸️ Уведомление ({error_type}) пропущено")
        return
    LAST_NOTIFY[error_type] = now
    try:
        vk.messages.send(
            user_id=ADMIN_ID,
            message=f"⚠️ Ошибка бота ({error_type}):\n{error_text}",
            random_id=get_random_id()
        )
        print(f"📨 Уведомление админу отправлено: {error_type}")
    except Exception as e:
        print(f"❌ Не удалось уведомить админа: {e}")

# === ПОИСК ===
def search_duckduckgo(query):
    try:
        print(f"🔍 Ищу в DuckDuckGo: {query}")
        results = DDGS().text(query, region='ru-ru', max_results=5, timelimit='m', backend='auto')
        if not results:
            print("🔍 Результатов не найдено.")
            return None
        context = ""
        for r in results:
            title = r.get('title', '')
            body = r.get('body', '')
            href = r.get('href', '')
            if title or body:
                context += f"【{title}】{body}\nИсточник: {href}\n\n"
        print(f"✅ Найдено {len(results)} результатов.")
        return context if context else None
    except Exception as e:
        print(f"❌ Ошибка поиска DuckDuckGo: {e}")
        return None

# === КУРС И ПОГОДА ===
def get_usd_rate():
    try:
        response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=5)
        data = response.json()
        if data and "Valute" in data and "USD" in data["Valute"]:
            return f"Курс доллара США: {data['Valute']['USD']['Value']:.2f} рублей"
    except:
        pass
    return None

def get_weather(city="Москва"):
    try:
        response = requests.get(f"https://wttr.in/{city}?format=%C+%t+%w&lang=ru", timeout=5)
        if response.status_code == 200:
            return f"Погода в {city}: {response.text.strip()}"
    except:
        pass
    return None

# === ОБРАБОТЧИК СООБЩЕНИЙ ===
def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '')
    print(f"📩 от {user_id}: {text}")

    if not text:
        return

    try:
        update_stats(user_id)
    except Exception as e:
        print(f"❌ Ошибка статистики: {e}")

    # === КОМАНДЫ ===
    if text == "/start" or text == "🌿 Главная":
        send_message(user_id, "🌿 Привет! Я Ботаник.\n\n"
                              "💰 Спроси курс доллара\n"
                              "🌤️ Узнай погоду\n"
                              "🔍 Или задай любой вопрос — я поищу в интернете")
        return

    if text == "/help" or text == "📋 Команды":
        send_message(user_id, "📋 Команды:\n/start — приветствие\n/stats — твоя статистика\n/clear — очистить историю\n/rules — правила\n/info — информация")
        return

    if text == "/stats" or text == "📊 Статистика":
        stats = load_stats()
        user_id_str = str(user_id)
        if user_id_str in stats:
            data = stats[user_id_str]
            send_message(user_id,
                f"📊 *Твоя статистика:*\n\n"
                f"💬 Сообщений: {data['messages']}\n"
                f"📅 Первое обращение: {data['first_seen']}\n"
                f"🕐 Последнее: {data['last_seen']}"
            )
        else:
            send_message(user_id, "📊 У тебя пока нет сообщений.")
        return

    if text == "/admin_stats":
        if user_id == ADMIN_ID:
            stats = load_stats()
            total_users = len(stats)
            total_messages = sum(u["messages"] for u in stats.values())
            send_message(user_id,
                f"📊 *Общая статистика:*\n\n"
                f"👥 Всего пользователей: {total_users}\n"
                f"💬 Всего сообщений: {total_messages}"
            )
        else:
            send_message(user_id, "⛔ У тебя нет прав для этой команды.")
        return

    if text == "/clear" or text == "🧹 Очистить":
        clear_history(user_id)
        send_message(user_id, "🧹 История диалога очищена. Начинаем с чистого листа!")
        return

    if text == "/rules" or text == "📜 Правила":
        send_message(user_id, "📜 Правила:\n1. Будь вежлив\n2. Не спамь\n3. Бот не хранит переписку")
        return

    if text == "/info" or text == "ℹ️ Инфо":
        send_message(user_id, f"🤖 Ботаник\n📌 Модель: {config.OPENAI_MODEL}\n📌 Поиск: DuckDuckGo")
        return

    lower_text = text.lower()

    # === КУРС ДОЛЛАРА ===
    if "курс" in lower_text and "доллар" in lower_text:
        rate = get_usd_rate()
        if rate:
            send_message(user_id, f"💰 {rate}")
            return
        else:
            send_message(user_id, "⚠️ Не удалось получить курс.")
            return

    # === ПОГОДА ===
    if "погод" in lower_text:
        city = "Москва"
        words = text.split()
        for word in words:
            if word.istitle() and len(word) > 2 and word not in ["Погода", "Какая"]:
                city = word
                break
        weather = get_weather(city)
        if weather:
            send_message(user_id, f"🌤️ {weather}")
            return
        else:
            send_message(user_id, f"⚠️ Не удалось получить погоду.")
            return

    # === ГИБРИДНЫЙ ОТВЕТ (ПОИСК + AI + ПАМЯТЬ) ===
    try:
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        search_triggers = ["что такое", "кто такой", "кто такая", "когда", "где ",
                          "новости", "сколько", "как работает", "почему",
                          "расскажи про", "найди", "погугли", "какой", "какая", "какие"]
        need_search = any(trigger in lower_text for trigger in search_triggers)
        
        search_context = None
        if need_search:
            search_context = search_duckduckgo(text)
        
        system_prompt = (
            f"Сегодня {now}. Ты — Ботаник, полезный AI-ассистент. "
            f"Отвечай на русском, кратко и по делу. Помни контекст диалога."
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(get_history(user_id))
        
        if search_context:
            messages.append({
                "role": "user",
                "content": f"Информация из интернета:\n{search_context}\n\nВопрос: {text}\n\nОтветь, используя эту информацию."
            })
            print("🤔 Формирую ответ с поиском...")
        else:
            messages.append({"role": "user", "content": text})
            print("🤔 Формирую ответ без поиска (диалог)...")
        
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            temperature=0.5,
            max_tokens=500,
        )
        answer = response.choices[0].message.content
        print(f"✅ Ответ: {answer[:50]}")
        
        add_to_history(user_id, "user", text)
        add_to_history(user_id, "assistant", answer)
        
        send_message(user_id, answer)
            
    except Exception as e:
        error_msg = f"Ошибка AI: {e}"
        print(f"❌ {error_msg}")
        notify_admin(error_msg, "ai")
        send_message(user_id, f"⚠️ Ошибка AI: {e}")

# === ЗАПУСК ===
def main():
    print(f"✅ Бот запущен. Группа ID: {config.GROUP_ID}")
    print(f"📌 Админ ID: {ADMIN_ID}")
    print("⏳ Ожидаю сообщения...")

    load_history()
    cleanup_old_history()

    while True:
        try:
            longpoll = VkBotLongPoll(vk_session, config.GROUP_ID)
            print("🔄 LongPoll подключён")
            for event in longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    handle_message(event)
        except Exception as e:
            error_msg = f"LongPoll упал: {e}"
            print(f"❌ {error_msg}")
            notify_admin(error_msg, "longpoll")
            print("⏳ Переподключение через 5 секунд...")
            time.sleep(5)
            continue

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("✅ Flask запущен")
    
    main()
