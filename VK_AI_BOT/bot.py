import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import config
import requests

vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("🌿 Главная", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("📋 Команды", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("ℹ️ Инфо", color=VkKeyboardColor.PRIMARY)
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
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return None

def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '')
    print(f"📩 от {user_id}: {text}")

    if not text:
        return

    if text == "/start" or text == "🌿 Главная":
        send_message(user_id, "🌿 Привет! Я Ботаник. Задавай любой вопрос, я поищу в интернете.")
        return

    if text == "/help" or text == "📋 Команды":
        send_message(user_id, "📋 Просто напиши вопрос, и я найду ответ в интернете.")
        return

    if text == "/clear" or text == "🧹 Очистить":
        send_message(user_id, "🧹 История очищена.")
        return

    if text == "/rules" or text == "📜 Правила":
        send_message(user_id, "📜 Правила: будь вежлив, не спамь.")
        return

    if text == "/info" or text == "ℹ️ Инфо":
        send_message(user_id, f"🤖 Ботаник\nСтатус: онлайн")
        return

    # === ПОИСК В ИНТЕРНЕТЕ ===
    send_message(user_id, "🔍 Ищу в интернете...")
    result = search_web(text)
    
    if result:
        send_message(user_id, f"🔍 {result}")
    else:
        send_message(user_id, "❌ Не нашёл информацию по этому запросу. Попробуй переформулировать.")

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
