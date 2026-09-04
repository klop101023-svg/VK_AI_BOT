import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import config
import requests
import json
import os
from datetime import datetime
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

# === ПОДКЛЮЧЕНИЕ GIGACHAT ===
try:
    client = GigaChat(
        base_url="https://api.giga.chat/v2",
        credentials=config.GIGACHAT_API_KEY,
        scope=config.GIGACHAT_SCOPE,
        verify_ssl_certs=False,
    )
    print("✅ GigaChat подключён")
except Exception as e:
    print(f"❌ Ошибка GigaChat: {e}")
    client = None

STATS_FILE = "/data/stats.json"
ADMIN_ID = 1027228715

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def update_stats(user_id):
    stats = load_stats()
    user_id_str = str(user_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if user_id_str not in stats:
        stats[user_id_str] = {
            "first_seen": now,
            "last_seen": now,
            "messages": 0
        }
    else:
        stats[user_id_str]["last_seen"] = now
    
    stats[user_id_str]["messages"] += 1
    save_stats(stats)

def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("🌿 Главная", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("📋 Команды", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📊 Статистика", color=VkKeyboardColor.PRIMARY)
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

def ask_gigachat(text):
    """Отправляет запрос в GigaChat"""
    if client is None:
        return "❌ GigaChat не подключён"
    
    try:
        messages = [
            Messages(role=MessagesRole.USER, content=text)
        ]
        
        chat = Chat(
            model="GigaChat-3-Ultra",
            messages=messages,
        )
        
        response = client.chat(chat)
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Ошибка GigaChat: {e}")
        return None

def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '')
    print(f"📩 от {user_id}: {text}")

    if not text:
        return

    update_stats(user_id)

    if text == "/start" or text == "🌿 Главная":
        send_message(user_id, "🌿 Привет! Я Ботаник.\n\n"
                              "💬 Я отвечаю через GigaChat\n"
                              "💰 Спроси курс доллара\n"
                              "🌤️ Узнай погоду\n"
                              "❓ Задай любой вопрос!")
        return

    if text == "/help" or text == "📋 Команды":
        send_message(user_id, "📋 Команды:\n/start — приветствие\n/stats — твоя статистика\n/clear — очистить историю\n/rules — правила\n/info — информация")
        return

    if text == "/stats" or text == "📊 Статистика":
        stats = load_stats()
        user_id_str = str(user_id)
        if user_id_str in stats:
            data = stats[user_id_str]
            send_message(user_id,
                f"📊 *Твоя статистика:*\n\n"
                f"💬 Сообщений: {data['messages']}\n"
                f"📅 Первое обращение: {data['first_seen']}\n"
                f"🕐 Последнее: {data['last_seen']}"
            )
        else:
            send_message(user_id, "📊 У тебя пока нет сообщений.")
        return

    if text == "/admin_stats":
        if user_id == ADMIN_ID:
            stats = load_stats()
            total_users = len(stats)
            total_messages = sum(u["messages"] for u in stats.values())
            send_message(user_id,
                f"📊 *Общая статистика:*\n\n"
                f"👥 Всего пользователей: {total_users}\n"
                f"💬 Всего сообщений: {total_messages}"
            )
        else:
            send_message(user_id, "⛔ У тебя нет прав для этой команды.")
        return

    if text == "/clear" or text == "🧹 Очистить":
        send_message(user_id, "🧹 История очищена.")
        return

    if text == "/rules" or text == "📜 Правила":
        send_message(user_id, "📜 Правила:\n1. Будь вежлив\n2. Не спамь\n3. Бот не хранит переписку")
        return

    if text == "/info" or text == "ℹ️ Инфо":
        send_message(user_id, f"🤖 Ботаник\n📌 Модель: GigaChat-3-Ultra")
        return

    # === ОТВЕТ ЧЕРЕЗ GIGACHAT ===
    send_message(user_id, "🤔 Думаю...")
    answer = ask_gigachat(text)
    
    if answer:
        send_message(user_id, answer)
    else:
        send_message(user_id, "⚠️ Ошибка. Попробуй позже.")

def main():
    print(f"✅ Бот запущен. Группа ID: {config.GROUP_ID}")
    print(f"📌 Админ ID: {ADMIN_ID}")
    print("📌 Модель: GigaChat-3-Ultra")
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
