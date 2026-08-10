import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import config

# === ПОДКЛЮЧЕНИЕ К ВК ===
vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

# === КЛАВИАТУРА ===
def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("📋 Команды", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("ℹ️ Инфо", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🧹 Очистить", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button("📜 Правила", color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()

# === ОТПРАВКА СООБЩЕНИЙ С КЛАВИАТУРОЙ ===
def send_message(user_id, text):
    try:
        vk.messages.send(
            user_id=user_id,
            message=text,
            keyboard=get_main_keyboard(),  # <--- КЛЮЧЕВАЯ СТРОКА
            random_id=get_random_id()
        )
    except Exception as e:
        print(f"❌ Ошибка: {e}")

# === ОБРАБОТКА СООБЩЕНИЙ ===
def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '')

    print(f"📩 от {user_id}: {text}")

    if text == "/start":
        send_message(user_id, "🌿 Привет! Я Ботаник. Вот твои кнопки:")
    elif text == "📋 Команды":
        send_message(user_id, "📋 Команды: /start, /help, /clear, /rules")
    elif text == "ℹ️ Инфо":
        send_message(user_id, "🤖 Ботаник — твой AI-помощник.")
    elif text == "🧹 Очистить":
        send_message(user_id, "🧹 История очищена (пока просто пример)")
    elif text == "📜 Правила":
        send_message(user_id, "📜 Будь вежлив. Бот не хранит переписку.")
    else:
        send_message(user_id, f"Ты написал: {text}\n\nИспользуй кнопки ниже.")

# === ЗАПУСК ===
def main():
    print("✅ Бот запущен. Ожидаю сообщения...")
    longpoll = VkBotLongPoll(vk_session, config.GROUP_ID)
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            handle_message(event)

if __name__ == "__main__":
    main()
