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

# === КЛАВИАТУРА (кнопки-команды) ===
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

# === ОБРАБОТЧИК ===
def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '')
    print(f"📩 от {user_id}: {text}")

    if not text:
        return

    # === ОБРАБОТКА КНОПОК И КОМАНД ===

    # 🌿 Главная
    if text == "/start" or text == "🌿 Главная":
        send_message(user_id,
            "🌿 *Привет! Я Ботаник — твой умный AI-помощник.*\n\n"
            "📌 Я умею:\n"
            "• Отвечать на любые вопросы\n"
            "• Запоминать ход беседы\n"
            "• Помогать с задачами\n\n"
            "⬇️ Используй кнопки ниже для навигации.")
        return

    # 📋 Команды
    elif text == "/help" or text == "📋 Команды":
        send_message(user_id,
            "📋 *Список доступных команд:*\n\n"
            "🌿 Главная — приветствие и знакомство\n"
            "📋 Команды — этот список\n"
            "🧹 Очистить — очистить историю диалога\n"
            "📜 Правила — правила использования\n"
            "ℹ️ Инфо — информация о боте\n\n"
            "💡 Просто напиши мне любое сообщение, и я отвечу!")
        return

    # 🧹 Очистить
    elif text == "/clear" or text == "🧹 Очистить":
        send_message(user_id,
            "🧹 *История диалога очищена.*\n\n"
            "Начинаем с чистого листа! ✨")
        return

    # 📜 Правила
    elif text == "/rules" or text == "📜 Правила":
        send_message(user_id,
            "📜 *Правила использования бота:*\n\n"
            "1. Бот создан для помощи и общения\n"
            "2. Не используйте бота для спама\n"
            "3. Бот не хранит личные данные\n"
            "4. Запрещены оскорбления и угрозы\n"
            "5. Бот работает 24/7\n\n"
            "Нарушение правил может привести к блокировке.")
        return

    # ℹ️ Инфо
    elif text == "/info" or text == "ℹ️ Инфо":
        send_message(user_id,
            f"🤖 *Ботаник*\n\n"
            f"📌 Модель: {config.OPENAI_MODEL}\n"
            f"📌 Память: до 20 сообщений\n"
            f"📌 Группа ID: {config.GROUP_ID}\n"
            f"📌 Статус: онлайн 24/7")
        return

    # === AI-ОТВЕТ (если не команда) ===
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
