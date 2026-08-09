import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
import openai
import config
import json
import os
from datetime import datetime, timedelta

# === ПОДКЛЮЧЕНИЕ К ВК ===
vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

# === ПОДКЛЮЧЕНИЕ К AITUNNEL ===
client = openai.OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL,
)

# === ПАМЯТЬ ДИАЛОГА ===
MEMORY_FILE = "dialogs.json"
MAX_MEMORY = 20  # сколько последних сообщений помнить

def load_memory(user_id):
    """Загружает историю диалога пользователя"""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(str(user_id), [])
    except:
        return []

def save_memory(user_id, messages):
    """Сохраняет историю диалога пользователя"""
    data = {}
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}
    
    data[str(user_id)] = messages[-MAX_MEMORY:]  # обрезаем до лимита
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clear_memory(user_id):
    """Очищает историю диалога пользователя"""
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

# === ОТПРАВКА СООБЩЕНИЙ ===
def send_message(user_id, text):
    try:
        vk.messages.send(
            user_id=user_id,
            message=text,
            random_id=get_random_id()
        )
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

def send_typing(user_id):
    """Показывает, что бот печатает"""
    try:
        vk.messages.setActivity(user_id=user_id, type="typing")
    except:
        pass

# === КОМАНДЫ ===
def handle_commands(user_id, text):
    if text == "/start":
        send_message(user_id, 
            "🌿 Привет! Я Ботаник — твой AI-помощник.\n\n"
            "📌 Я умею:\n"
            "• Отвечать на вопросы\n"
            "• Запоминать диалог\n"
            "• Помогать с задачами\n\n"
            "❓ Напиши /help для списка команд.")
        return True

    elif text == "/help":
        send_message(user_id,
            "📋 Список команд:\n\n"
            "/start — приветствие\n"
            "/help — помощь\n"
            "/clear — очистить историю\n"
            "/info — информация о боте\n\n"
            "💡 Просто напиши мне что-нибудь!")
        return True

    elif text == "/clear":
        clear_memory(user_id)
        send_message(user_id, "🧹 История диалога очищена!")
        return True

    elif text == "/info":
        send_message(user_id,
            f"🤖 Ботаник\n"
            f"📌 Модель: {config.OPENAI_MODEL}\n"
            f"📌 Память: до {MAX_MEMORY} сообщений\n"
            f"📌 Группа ID: {config.GROUP_ID}")
        return True

    return False

# === ГЛАВНЫЙ ОБРАБОТЧИК ===
def handle_message(event):
    if event.from_user:
        user_id = event.object.message['from_id']
        source = "личные"
    elif event.from_chat:
        user_id = event.object.message['from_id']
        source = "группа"
    else:
        return

    text = event.object.message.get('text', '')
    print(f"📩 [{source}] от {user_id}: {text}")

    if not text:
        return

    # === ОБРАБОТКА КОМАНД ===
    if text.startswith('/'):
        if handle_commands(user_id, text):
            return

    # === ЗАГРУЗКА ПАМЯТИ ===
    history = load_memory(user_id)
    messages = [
        {"role": "system", "content": "Ты — Ботаник. Умный, но без занудства. Отвечай кратко и по делу. Используй эмодзи, но не перебарщивай. Если не знаешь ответа — так и скажи."}
    ]
    messages.extend(history)
    messages.append({"role": "user", "content": text})

    # === ОТПРАВКА В AI ===
    try:
        send_typing(user_id)

        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )

        answer = response.choices[0].message.content
        print(f"🤖 Ответ для {user_id}: {answer}")

        # === СОХРАНЕНИЕ ПАМЯТИ ===
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": answer})
        save_memory(user_id, history)

        send_message(user_id, answer)

    except Exception as e:
        print(f"❌ Ошибка AI: {e}")
        send_message(user_id, "⚠️ Извините, произошла ошибка. Попробуйте позже.")

# === ЗАПУСК ===
def main():
    print(f"✅ Бот запущен. Группа ID: {config.GROUP_ID}")
    print(f"📌 Модель: {config.OPENAI_MODEL}")
    print(f"📌 Память: до {MAX_MEMORY} сообщений")
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
