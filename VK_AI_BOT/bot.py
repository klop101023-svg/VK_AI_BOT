import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
import config
import requests

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

def get_usd_rate():
    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data and "Valute" in data and "USD" in data["Valute"]:
            return f"Курс доллара США: {data['Valute']['USD']['Value']:.2f} рублей"
    except Exception as e:
        return f"❌ Ошибка: {e}"
    return None

def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '')
    print(f"📩 от {user_id}: {text}")

    if not text:
        return

    if "курс" in text.lower() or "доллар" in text.lower():
        rate = get_usd_rate()
        if rate:
            send_message(user_id, f"💰 {rate}")
        else:
            send_message(user_id, "⚠️ Не удалось получить курс")
        return

    send_message(user_id, f"Ты написал: {text}")

def main():
    print(f"✅ Тестовый бот запущен. Группа ID: {config.GROUP_ID}")
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
