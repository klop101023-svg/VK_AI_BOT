import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
import openai
import config
import time

# === ПОДКЛЮЧЕНИЕ К ВК ===
vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

# === ПОДКЛЮЧЕНИЕ К AITUNNEL (вместо OpenRouter) ===
client = openai.OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL,
)

# === ФУНКЦИЯ ОТПРАВКИ СООБЩЕНИЯ ===
def send_message(user_id, text):
    try:
        vk.messages.send(
            user_id=user_id,
            message=text,
            random_id=get_random_id()
        )
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

# === ОБРАБОТКА СООБЩЕНИЙ ===
def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '')

    print(f"📩 Новое сообщение от {user_id}: {text}")

    if not text:
        return

    # === ЗАПРОС К AITUNNEL ===
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Ты — полезный и дружелюбный помощник. Отвечай кратко и по делу."},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=500,
        )

        answer = response.choices[0].message.content
        print(f"🤖 Ответ: {answer}")
        send_message(user_id, answer)

    except Exception as e:
        print(f"❌ Ошибка AI: {e}")
        send_message(user_id, "⚠️ Произошла ошибка. Попробуй позже.")

# === ЗАПУСК ===
def main():
    print(f"✅ Бот запущен. Группа ID: {config.GROUP_ID}")
    print("⏳ Ожидаю сообщения...")

    try:
        longpoll = VkBotLongPoll(vk_session, config.GROUP_ID)
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                handle_message(event)
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print("Проверь настройки ВК: Long Poll API и токен.")

if __name__ == "__main__":
    main()