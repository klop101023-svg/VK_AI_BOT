import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import config  # Импортируем ваши настройки
import requests
import json
import os
from datetime import datetime


# === ПОДКЛЮЧЕНИЕ VK И НАСТРОЙКИ ===

vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

STATS_FILE = "/data/stats.json"
ADMIN_ID = 1027228715

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
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
            keyboard=keyboard or get_main_keyboard(),
            random_id=get_random_id()
        )
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")


# === ПОДКЛЮЧЕНИЕ К GIGACHAT ===

def init_gigachat_client():
    """Создаёт клиента только один раз"""
    base_url = "https://developers.sber.ru/api/gigachat/v1/chat/completions"
    credentials = config.GIGACHAT_API_KEY
    scope = config.GIGACHAT_SCOPE

    # Проверим наличие ключей
    if not all([base_url, credentials, scope]):
        raise ValueError("Не хватает настроек для GigaChat!")

    from gigachat import GigaChat
    from gigachat.models import Chat, Messages, MessagesRole

    client = GigaChat(base_url=base_url, credentials=credentials, scope=scope)
    print("✅ GigaChat подключён.")
    return client

client = None  # Глобальная переменная для хранения клиента

try:
    client = init_gigachat_client()  # Пробуем создать клиент сразу после импорта
except Exception as e:
    print(f"❌ Не удалось подключить GigaChat: {str(e)}")


# === ОБРАБОТКА ЗАПРОСА ===

def ask_gigachat(text):
    """
    Отправляет запрос в GigaChat.
    Теперь мы передаём доступ к навыку web_search, чтобы бот искал ответы в интернете.
    """
    global client  # Используем глобальную переменную

    if client is None:
        return "🛑 GigaChat недоступен."

    messages = [
        Messages(role=MessagesRole.USER, content=text),
    ]

    chat = Chat(
        model="GigaChat-3-Ultra",
        messages=messages,
        available_functions=["web_search"],  # <--- ВНИМАНИЕ! Это ключ к актуальным ответам!
    )

    try:
        response = client.chat(chat)
        answer = response.choices[0].message.content.strip()
        return answer[:4096]  # Ограничение длины ответа ВК
    except Exception as e:
        print(f"❌ Ошибка запроса к GigaChat: {type(e).__name__}: {str(e)}")
        return None


# === КОМАНДЫ БОТА ===

def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '').strip()

    if not text:
        return

    update_stats(user_id)  # Обновляем статистику

    # Системные команды
    if text == "/start" or text.startswith("🌿"):
        send_message(user_id, "🌿 Привет! Я Ботаник.\n\n💬 Я отвечаю через GigaChat\n💰 Спроси курс доллара\n🌤️ Узнай погоду\n❓ Задай любой вопрос!")
        return

    if text == "/help" or text.startswith("📋"):
        send_message(user_id, "📋 Команды:\n/start — приветствие\n/stats — твоя статистика\n/clear — очистить историю\n/rules — правила\n/info — информация")
        return

    if text == "/stats" or text.startswith("📊"):
        stats = load_stats()
        user_id_str = str(user_id)
        data = stats.get(user_id_str, {})
        msg = (
            f"📊 *Твоя статистика:*\n\n"
            f"💬 Сообщений: {data.get('messages', 0)}\n"
            f"📅 Первое обращение: {data.get('first_seen', '—')}\n"
            f"🕐 Последнее: {data.get('last_seen', '—')}"
        )
        send_message(user_id, msg)
        return

    if text == "/admin_stats":
        if user_id != ADMIN_ID:
            send_message(user_id, "⛔ У тебя нет прав для этой команды.")
            return

        stats = load_stats()
        total_users = len(stats)
        total_messages = sum(u["messages"] for u in stats.values())
        
        msg = (
            f"📊 *Общая статистика:*\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"💬 Всего сообщений: {total_messages}"
        )
        send_message(user_id, msg)
        return

    if text == "/clear" or text.startswith("🧹"):
        send_message(user_id, "🧹 История очищена.")  # На самом деле история не хранится, так что это просто заглушка
        return

    if text == "/rules" or text.startswith("📜"):
        send_message(user_id, "📜 Правила:\n1. Будь вежлив\n2. Не спамь\n3. Бот не хранит переписку")
        return

    if text == "/info" or text.startswith("ℹ️"):
        send_message(user_id, f"🤖 Ботаник\n📌 Модель: GigaChat-3-Ultra")
        return

    # Основной функционал — отправка вопроса в GigaChat
    send_message(user_id, "🤔 Думаю...")
    answer = ask_gigachat(text)

    if answer:
        send_message(user_id, answer)
    else:
        send_message(user_id, "🛑 Что-то пошло не так. Попробуй позже.")


# === ЛОНГПОЛЛ ===

def main():
    print(f"✅ Бот запущен. Группа ID: {config.GROUP_ID}")
    print(f"📌 Админ ID: {ADMIN_ID}")
    print("📌 Модель: GigaChat-3-Ultra")
    print("⏳ Ожидаю сообщения...")

    longpoll = VkBotLongPoll(vk_session, group_id=config.GROUP_ID)
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
            handle_message(event)

if __name__ == "__main__":
    main()
