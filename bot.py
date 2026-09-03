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

vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

client = openai.OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL,
)

STATS_FILE = "/data/stats.json"
ADMIN_ID = 1027228715

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

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
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def search_searxng(query):
    """Ищет через SearXNG — пробует несколько инстансов"""
    instances = [
        "https://searx.space/search",
        "https://search.gresmash.com/search",
        "https://searx.nd.ax/search",
        "https://searx.be/search"
    ]
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for url in instances:
        try:
            params = {"q": query, "format": "json", "categories": "general", "language": "ru"}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    result = data["results"][0]
                    return f"🔍 {result.get('title', '')}\n{result.get('snippet', '')}\n🔗 {result.get('url', '')}"
        except:
            continue
    return None

def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '')
    print(f"📩 от {user_id}: {text}")

    if not text:
        return

    update_stats(user_id)

    if text == "/start" or text == "🌿 Главная":
        send_message(user_id, "🌿 Привет! Я Ботаник.\n\n🔍 Задай любой вопрос — я поищу в интернете.\n💰 Спроси курс доллара\n🌤️ Узнай погоду")
        return

    if text == "/help" or text == "📋 Команды":
        send_message(user_id, "📋 Команды:\n/start — приветствие\n/stats — твоя статистика\n/clear — очистить историю\n/rules — правила\n/info — информация")
        return

    if text == "/stats" or text == "📊 Статистика":
        stats = load_stats()
        user_id_str = str(user_id)
        if user_id_str in stats:
            data = stats[user_id_str]
            send_message(user_id, f"📊 *Твоя статистика:*\n\n💬 Сообщений: {data['messages']}\n📅 Первое обращение: {data['first_seen']}\n🕐 Последнее: {data['last_seen']}")
        else:
            send_message(user_id, "📊 У тебя пока нет сообщений.")
        return

    if text == "/admin_stats":
        if user_id == ADMIN_ID:
            stats = load_stats()
            total_users = len(stats)
            total_messages = sum(u["messages"] for u in stats.values())
            send_message(user_id, f"📊 *Общая статистика:*\n\n👥 Всего пользователей: {total_users}\n💬 Всего сообщений: {total_messages}")
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
        send_message(user_id, f"🤖 Ботаник\n📌 Поиск: SearXNG\n📌 Модель: {config.OPENAI_MODEL}")
        return

    # === ПОИСК В ИНТЕРНЕТЕ ===
    send_message(user_id, "🔍 Ищу в интернете...")
    result = search_searxng(text)

    if result:
        send_message(user_id, result)
        return

    # === ЕСЛИ НЕ НАШЁЛ — AI ===
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": text}],
            temperature=0.7,
            max_tokens=500,
        )
        send_message(user_id, f"💡 {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Ошибка AI: {e}")
        send_message(user_id, "⚠️ Ошибка. Попробуй позже.")

def main():
    print(f"✅ Бот запущен. Группа ID: {config.GROUP_ID}")
    print("⏳ Ожидаю сообщения...")

    try:
        longpoll = VkBotLongPoll(vk_session, config.GROUP_ID)
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                handle_message(event)
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
