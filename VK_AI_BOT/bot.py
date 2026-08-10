import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import openai
import config
import json
import os

# === ПОДКЛЮЧЕНИЕ К ВК ===
vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

# === ПОДКЛЮЧЕНИЕ К AITUNNEL ===
client = openai.OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL,
)

# === ПАМЯТЬ ===
MEMORY_FILE = "dialogs.json"
MAX_MEMORY = 20

def load_memory(user_id):
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(str(user_id), [])
    except:
        return []

def save_memory(user_id, messages):
    data = {}
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}
    data[str(user_id)] = messages[-MAX_MEMORY:]
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clear_memory(user_id):
    data = {}
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}
    if str(user_id) in data:
        del data[str(user_id)]
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === КЛАВИАТУРА ===
def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("📋 Команды", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("ℹ️ Инфо", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🧹 Очистить", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button("📜 Правила", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📋 Все команды", color=VkKeyboardColor.PRIMARY)
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

def send_typing(user_id):
    try:
        vk.messages.setActivity(user_id=user_id, type="typing")
    except:
        pass

# === КОМАНДЫ (и кнопки, которые их вызывают) ===
def handle_commands(user_id, text):
    # /start
    if text == "/start":
        send_message(user_id,
            "🌿 Привет! Я Ботаник — твой умный AI-помощник.\n\n"
            "📌 Используй кнопки ниже для навигации.")
        return True

    # /help или кнопка "📋 Все команды"
    elif text == "/help" or text == "📋 Все команды":
        send_message(user_id,
            "📋 *Список всех команд:*\n\n"
            "/start — приветствие\n"
            "/help — этот список\n"
            "/clear — очистить историю\n"
            "/rules — правила\n"
            "/info — информация\n\n"
            "💡 Или просто напиши мне что угодно!")
        return True

    # /clear или кнопка "🧹 Очистить"
    elif text == "/clear" or text == "🧹 Очистить":
        clear_memory(user_id)
        send_message(user_id, "🧹 История диалога очищена. Начинаем с чистого листа!")
        return True

    # /rules или кнопка "📜 Правила"
    elif text == "/rules" or text == "📜 Правила":
        send_message(user_id,
            "📜 *Правила использования:*\n\n"
            "1. Бот создан для помощи и общения\n"
            "2. Не используйте бота для спама\n"
            "3. Бот не хранит личные данные\n"
            "4. Запрещены оскорбления и угрозы\n"
            "5. Бот работает 24/7\n\n"
            "Нарушение правил может привести к блокировке.")
        return True

    # /info или кнопка "ℹ️ Инфо"
    elif text == "/info" or text == "ℹ️ Инфо":
        send_message(user_id,
            f"🤖 *Ботаник*\n"
            f"📌 Модель: {config.OPENAI_MODEL}\n"
            f"📌 Память: до {MAX_MEMORY} сообщений\n"
            f"📌 Статус: онлайн 24/7")
        return True

    return False

# === ОСНОВНОЙ ОБРАБОТЧИК ===
def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '')
    print(f"📩 от {user_id}: {text}")

    if not text:
        return

    # === КНОПКИ И КОМАНДЫ ===
    if text.startswith('/') or text in ["📋 Команды", "ℹ️ Инфо", "🧹 Очистить", "📜 Правила", "📋 Все команды"]:
        if handle_commands(user_id, text):
            return

    # === AI-ОТВЕТ ===
    history = load_memory(user_id)
    messages = [
        {"role": "system", "content": "Ты — Ботаник. Отвечай кратко и по делу. Используй эмодзи."}
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": text})

    try:
        send_typing(user_id)
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        answer = response.choices[0].message.content
        print(f"🤖 Ответ: {answer}")

        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": answer})
        save_memory(user_id, history)

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
