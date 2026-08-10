import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import openai
import config

vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

client = openai.OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL,
)

# === КЛАВИАТУРА ===
def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("📋 Команды", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("ℹ️ Инфо", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🧹 Очистить", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button("📜 Правила", color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()

# === ОТПРАВКА ===
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

# === ОБРАБОТКА ===
def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '')
    print(f"📩 от {user_id}: {text}")

    if not text:
        return

    # === ОБРАБОТКА КНОПОК ===
    if text == "📋 Команды":
        send_message(user_id, "📋 /help — список команд\n/start — приветствие\n/clear — очистить\n/rules — правила")
        return

    elif text == "ℹ️ Инфо":
        send_message(user_id, f"🤖 Ботаник\nМодель: {config.OPENAI_MODEL}\nСтатус: онлайн")
        return

    elif text == "🧹 Очистить":
        send_message(user_id, "🧹 История очищена (функция будет позже)")
        return

    elif text == "📜 Правила":
        send_message(user_id, "📜 Будь вежлив. Бот не хранит переписку.")
        return

    # === AI-ОТВЕТ ===
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": text}],
            temperature=0.7,
            max_tokens=500,
        )
        answer = response.choices[0].message.content
        send_message(user_id, answer)

    except Exception as e:
        print(f"❌ Ошибка AI: {e}")
        send_message(user_id, "⚠️ Ошибка. Попробуй позже.")

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

if __name__ == "__main__":
    main()
