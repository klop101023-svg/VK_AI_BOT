import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import config
import requests
import json
import os
from datetime import datetime

vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

# === СТАТИСТИКА ===
STATS_FILE = "stats.json"
ADMIN_ID = 1027228715  # ЗАМЕНИ НА СВОЙ VK ID

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
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def search_web(query):
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("AbstractText"):
            return data["AbstractText"]
        if data.get("RelatedTopics"):
            for topic in data["RelatedTopics"]:
                if "Text" in topic:
                    return topic["Text"]
        return None
    except:
        return None

def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '')
    print(f"📩 от {user_id}: {text}")

    if not text:
        return

    update_stats(user_id)

    if text == "/start" or text == "🌿 Главная":
        send_message(user_id, "🌿 Привет! Я Ботаник. Задай любой вопрос, я поищу в интернете.\n\n📊 Статистика: /stats")
        return

    if text == "/help" or text == "📋 Команды":
        send_message(user_id, "📋 Команды:\n/start — приветствие\n/stats — твоя статистика\n/clear — очистить историю\n/rules — правила\n/info — информация\n\n💡 Просто задай вопрос — я найду ответ в интернете.")
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
        clear_memory(user_id)
        send_message(user_id, "🧹 История диалога очищена.")
        return

    if text == "/rules" or text == "📜 Правила":
        send_message(user_id, "📜 Правила:\n1. Будь вежлив\n2. Не спамь\n3. Бот не хранит переписку")
        return

    if text == "/info" or text == "ℹ️ Инфо":
        send_message(user_id, f"🤖 Ботаник\n📌 Модель: {config.OPENAI_MODEL}\n📌 Статус: онлайн\n📌 Поиск: интернет")
        return

    send_message(user_id, "🔍 Ищу...")
    result = search_web(text)

    if result:
        send_message(user_id, f"🔍 {result}")
    else:
        send_message(user_id, "❌ Не нашёл. Попробуй переформулировать.")

def main():
    print(f"✅ Бот запущен. Группа ID: {config.GROUP_ID}")
    print(f"📌 Статистика: включена")
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
