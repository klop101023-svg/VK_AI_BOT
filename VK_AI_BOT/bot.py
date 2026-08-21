import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
import config
import requests
import json

vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

def send_message(user_id, text):
    try:
        vk.messages.send(
            user_id=user_id,
            message=text,
            random_id=get_random_id()
        )
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def search_duckduckgo(query):
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("AbstractText"):
            return data["AbstractText"]
        
        if data.get("RelatedTopics"):
            for topic in data["RelatedTopics"]:
                if "Text" in topic:
                    return topic["Text"]
        
        return None
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return None

def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '')
    print(f"📩 от {user_id}: {text}")

    if not text:
        return

    if text == "/start":
        send_message(user_id, "🌿 Привет! Я Ботаник. Задай любой вопрос.")
        return

    send_message(user_id, "🔍 Ищу в интернете...")
    result = search_duckduckgo(text)
    
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
