import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import openai
import config
import json
import os
import requests
from datetime import datetime

vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

client = openai.OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL,
)

# === ПАМЯТЬ ===
DATA_DIR = "/data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

MEMORY_FILE = os.path.join(DATA_DIR, "dialogs.json")
MAX_MEMORY = 40

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

def send_typing(user_id):
    try:
        vk.messages.setActivity(user_id=user_id, type="typing")
    except:
        pass

# === ПОИСК В ИНТЕРНЕТЕ ===
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
    except:
        return None

# === АНАЛИЗ ЗАПРОСА: НУЖЕН ЛИ ПОИСК? ===
def need_search(query):
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Ты — анализатор запросов. Определи, нужна ли актуальная информация из интернета, чтобы ответить на вопрос пользователя. Если нужна — ответь только 'да'. Если не нужна — 'нет'."},
                {"role": "user", "content": f"Вопрос: {query}"}
            ],
            temperature=0.1,
            max_tokens=5,
        )
        answer = response.choices[0].message.content.lower().strip()
        return "да" in answer
    except:
        return False

# === КОМАНДЫ ===
def handle_commands(user_id, text):
    if text == "/start" or text == "🌿 Главная":
        send_message(user_id,
            "🌿 Привет! Я Ботаник — твой умный AI-помощник.\n\n"
            "📌 Я умею:\n"
            "• Отвечать на любые вопросы\n"
            "• Искать актуальную информацию в интернете\n"
            "• Запоминать ход беседы\n\n"
            "❓ Напиши /help, чтобы увидеть все команды.")
        return True

    elif text == "/help" or text == "📋 Команды":
        send_message(user_id,
            "📋 *Список команд:*\n\n"
            "/start — приветствие\n"
            "/help — этот список\n"
            "/clear — очистить историю\n"
            "/rules — правила\n"
            "/info — информация\n\n"
            "💡 Просто задай любой вопрос — я сам решу, искать ответ в интернете или ответить из своих знаний.")
        return True

    elif text == "/clear" or text == "🧹 Очистить":
        clear_memory(user_id)
        send_message(user_id, "🧹 История диалога очищена.")
        return True

    elif text == "/rules" or text == "📜 Правила":
        send_message(user_id,
            "📜 *Правила:*\n\n"
            "1. Бот создан для помощи\n"
            "2. Не спамьте\n"
            "3. Бот не хранит переписку\n"
            "4. Запрещены оскорбления\n"
            "5. Бот работает 24/7")
        return True

    elif text == "/info" or text == "ℹ️ Инфо":
        send_message(user_id,
            f"🤖 *Ботаник*\n"
            f"📌 Модель: {config.OPENAI_MODEL}\n"
            f"📌 Память: {MAX_MEMORY} сообщений\n"
            f"📌 Поиск: автоматический\n"
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

    if text == "start" or text == "начать":
        send_message(user_id, "🌿 Привет! Я Ботаник. Задавай любой вопрос.")
        return

    if text.startswith('/') or text in ["🌿 Главная", "📋 Команды", "ℹ️ Инфо", "🧹 Очистить", "📜 Правила"]:
        if handle_commands(user_id, text):
            return

    send_typing(user_id)

    # === АНАЛИЗ: НУЖЕН ЛИ ПОИСК? ===
    if need_search(text):
        send_message(user_id, "🔍 Ищу актуальную информацию...")
        search_result = search_web(text)
        if search_result:
            answer = f"🔍 *Актуальная информация:*\n\n{search_result}\n\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            send_message(user_id, answer)
            return
        else:
            send_message(user_id, "🔍 Не удалось найти информацию. Отвечаю из своих знаний...")

    # === AI-ОТВЕТ ===
    try:
        history = load_memory(user_id)
        messages = [
            {"role": "system", "content": "Ты — Ботаник, умный AI-помощник. Отвечай на русском языке, кратко, по делу, с лёгким юмором. Если не знаешь — честно скажи об этом."}
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": text})

        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        answer = response.choices[0].message.content

        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": answer})
        save_memory(user_id, history)

        send_message(user_id, answer)

    except Exception as e:
        print(f"❌ Ошибка AI: {e}")
        send_message(user_id, "⚠️ Произошла ошибка. Попробуйте позже.")

# === ЗАПУСК ===
def main():
    print(f"✅ Бот запущен. Группа ID: {config.GROUP_ID}")
    print(f"📌 Память: до {MAX_MEMORY} сообщений")
    print(f"📌 Поиск: автоматический (AI определяет)")
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
