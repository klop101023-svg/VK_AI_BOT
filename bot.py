import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
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

def send_message(user_id, text):
    try:
        vk.messages.send(
            user_id=user_id,
            message=text,
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

    if text == "/start":
        send_message(user_id, "🌿 Привет! Я Ботаник. Задай любой вопрос, я поищу в интернете.\n\n📊 Статистика: /stats")
        return

    if text == "/stats":
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

    send_message(user_id, "🔍 Ищу...")
    result = search_web(text)

    if result:
        send_message(user_id, f"🔍 {result}")
    else:
        send_message(user_id, "❌ Не нашёл. Попробуй переформулировать.")

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
