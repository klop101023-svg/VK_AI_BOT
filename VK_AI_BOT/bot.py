import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import config
import requests
import urllib.parse

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

def search_google(query):
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
        url = f"https://wttr.in/{city}?format=%C+%t+%w"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return f"Погода в {city}: {response.text.strip()}"
    except:
        pass
    return None

def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '')
    print(f"📩 от {user_id}: {text}")

    if not text:
        return

    if text == "/start" or text == "🌿 Главная":
        send_message(user_id, "🌿 Привет! Я Ботаник. Задавай любой вопрос, я найду в интернете.")
        return

    if text == "/help" or text == "📋 Команды":
        send_message(user_id, "📋 Просто напиши вопрос.")
        return

    if text == "/clear" or text == "🧹 Очистить":
        send_message(user_id, "🧹 История очищена.")
        return

    if text == "/rules" or text == "📜 Правила":
        send_message(user_id, "📜 Правила: будь вежлив.")
        return

    if text == "/info" or text == "ℹ️ Инфо":
        send_message(user_id, f"🤖 Ботаник\n📌 Поиск: интернет\n📌 Статус: онлайн")
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
        for word in text.split():
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

    # === УНИВЕРСАЛЬНЫЙ ПОИСК ===
    send_message(user_id, "🔍 Ищу в интернете...")
    result = search_google(text)

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
