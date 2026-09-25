import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import config
import requests
import json
import os
from datetime import datetime
import openai
from flask import Flask
import threading

# === ПОДКЛЮЧЕНИЕ К ВК ===
vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

# === ПОДКЛЮЧЕНИЕ К AITUNNEL ===
client = openai.OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL,
)

# === ФАЙЛ СТАТИСТИКИ (в папке с ботом) ===
STATS_FILE = "stats.json"
ADMIN_ID = 1027228715

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
        stats[user_id_str] = {
            "first_seen": now,
            "last_seen": now,
            "messages": 0
        }
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

def send_message(user_id, text, keyboard=None):
    try:
        vk.messages.send(
            user_id=user_id,
            message=text,
            keyboard=keyboard if keyboard else get_main_keyboard(),
            random_id=get_random_id()
        )
        print(f"✅ Отправлено: {text[:50]}")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

# === КУРС И ПОГОДА ===
def get_usd_rate():
    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data and "Valute" in data and "USD" in data["Valute"]:
            return f"Курс доллара США: {data['Valute']['USD']['Value']:.2f} рублей"
    except:
        pass
    return None

def get_weather(city="Москва"):
    try:
        url = f"https://wttr.in/{city}?format=%C+%t+%w&lang=ru"
        response = requests.get(url, timeout=5)
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

    # Сначала отвечаем, потом считаем статистику
    try:
        update_stats(user_id)
    except Exception as e:
        print(f"❌ Ошибка статистики: {e}")

    # === КОМАНДЫ ===
    if text == "/start" or text == "🌿 Главная":
        send_message(user_id, "🌿 Привет! Я Ботаник.\n\n"
                              "💰 Спроси курс доллара\n"
                              "🌤️ Узнай погоду\n"
                              "💬 Или просто поговори со мной")
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
        send_message(user_id, "🧹 История очищена.")
        return

    if text == "/rules" or text == "📜 Правила":
        send_message(user_id, "📜 Правила:\n1. Будь вежлив\n2. Не спамь\n3. Бот не хранит переписку")
        return

    if text == "/info" or text == "ℹ️ Инфо":
        send_message(user_id, f"🤖 Ботаник\n📌 Модель: {config.OPENAI_MODEL}\n📌 Статус: онлайн")
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

    # === AI-ОТВЕТ ===
    try:
        print("🤔 Отправляю запрос в AITUNNEL...")
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": text}],
            temperature=0.7,
            max_tokens=500,
        )
        answer = response.choices[0].message.content
        print(f"✅ Ответ получен: {answer[:50]}")
        send_message(user_id, answer)
    except Exception as e:
        print(f"❌ Ошибка AI: {e}")
        send_message(user_id, f"⚠️ Ошибка AI: {e}")

# === ЗАПУСК ===
def main():
    print(f"✅ Бот запущен. Группа ID: {config.GROUP_ID}")
    print(f"📌 Админ ID: {ADMIN_ID}")
    print("⏳ Ожидаю сообщения...")

    try:
        longpoll = VkBotLongPoll(vk_session, config.GROUP_ID)
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                handle_message(event)
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("✅ Flask запущен")
    
    # Запускаем бота
    main()
