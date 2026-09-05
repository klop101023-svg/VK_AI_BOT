import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import config  # Импортируйте свои переменные окружения из config.py
import requests
import json
import os
from datetime import datetime


# === НАСТРОЙКИ БОТА ===

VK_TOKEN = config.VK_TOKEN
GROUP_ID = config.GROUP_ID
ADMIN_ID = 1027228715

GIGACHAT_API_KEY = config.GIGACHAT_API_KEY
GIGACHAT_MODEL = "GigaChat-3-Ultra"
GIGACHAT_URL = "https://developers.sber.ru/api/gigachat/v1/chat/completions"
STATS_FILE = "/data/stats.json"

# ⚠️ ВАЖНО! Перемещаем сюда, чтобы сессия создавалась сразу при импорте модуля
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()


# === ПОДКЛЮЧЕНИЕ К GIGACHAT (прямой HTTP-запрос) ===

def ask_gigachat(text):
    """Отправляет запрос напрямую в API GigaChat."""
    
    if not text.strip():  # Проверяем, что пользователь прислал не пустое сообщение
        return "🛑 Пустая строка."

    payload = {
        "model": GIGACHAT_MODEL,
        "messages": [{"role": "user", "content": text}],
        "available_functions": ["web_search"]  # Без этого не будет актуальных ответов!
    }

    headers = {"Authorization": f"Bearer {GIGACHAT_API_KEY}"}

    try:
        response = requests.post(GIGACHAT_URL, json=payload, headers=headers)
        
        # Теперь мы видим РЕАЛЬНУЮ ошибку сервера!
        if response.status_code != 200:
            print(f"\n❌ Ошибка GigaChat ({response.status_code})")
            error_data = response.json()
            print(json.dumps(error_data, ensure_ascii=False, indent=2))
            
            # Типичные ошибки:
            # - code:401, message:"Unauthorized" → неверный ключ
            # - detail:"Access denied to the skill 'web_search'" → нет прав на навык
            return "🛑 Не удалось подключиться к GigaChat."
        
        answer = response.json().get("choices")[0].get("message").get("content")
        return answer[:4096]  # Ограничение длины ответа ВК

    except Exception as e:
        print(f"\n❌ Ошибка запроса: {type(e).__name__}: {e}")
        return None


# === СТАТИСТИКА ИСХОДНЫХ СООБЩЕНИЙ ===

def load_stats():
    stats = {}
    if not os.path.exists(STATS_FILE):
        return stats
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        stats.update(json.load(f))
    return stats

def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def update_stats(user_id):
    user_id_str = str(user_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    stats = load_stats()
    if user_id_str not in stats:
        stats[user_id_str] = {
            "first_seen": now,
            "last_seen": now,
            "messages": 1
        }
    else:
        stats[user_id_str]["last_seen"] = now
        stats[user_id_str]["messages"] += 1
    
    save_stats(stats)


# === ОБРАБОТКА КОМАНД ===

def send_message(user_id, text, keyboard=None):
    vk.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        message=text,
        keyboard=(keyboard or get_main_keyboard())
    )

def get_main_keyboard():
    kb = VkKeyboard(one_time=False)
    kb.add_button("🌿 Главная", color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button("📊 Статистика", color=VkKeyboardColor.SECONDARY)
    kb.add_button("ℹ️ Инфо", color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

def handle_message(event):
    user_id = event.object.message["from_id"]
    text = event.object.message.get("payload") or event.object.message.get("text", "").strip()

    update_stats(user_id)

    # Системные команды
    if text == "/start" or text.startswith("🌿"):
        send_message(user_id, "🌿 Привет! Я Ботаник.\n\n💬 Задавайте любые вопросы!")
    elif text == "/help":
        send_message(user_id, "📋 Команды:\n/start — приветствие\n/stats — статистика\n/clear — очистить историю\n/rules — правила\n/info — информация")
    elif text == "/stats" or text.startswith("📊"):  # Обычная статистика
        stats = load_stats()
        data = stats.get(str(user_id), {})
        msg = (
            "*Ваша статистика:*\n"
            f"💬 Сообщений: {data.get('messages', 0)}\n"
            f"📅 Первое обращение: {data.get('first_seen', '-')}\n"
            f"🕐 Последнее: {data.get('last_seen', '-')}"
        )
        send_message(user_id, msg)
    elif text == "/admin_stats":  # Исправлена логика админ-команды
        if user_id != ADMIN_ID:
            send_message(user_id, "⛔ У вас нет прав.")
            return

        stats = load_stats()
        total_users = len(stats)
        total_messages = sum(u["messages"] for u in stats.values())
        msg = (
            "*Общая статистика:*\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"💬 Всего сообщений: {total_messages}"
        )
        send_message(user_id, msg)
    elif text == "/clear" or text.startswith("🧹"):
        send_message(user_id, "🧹 История очищена.")  # На самом деле история не хранится
    elif text == "/rules" or text.startswith("📜"):
        send_message(user_id, "📜 Правила:\n1. Будьте вежливы.\n2. Не спамьте.")
    elif text == "/info" or text.startswith("ℹ️"):
        send_message(user_id, f"ℹ️ Модель: *{GIGACHAT_MODEL}*")
    else:
        # Основной функционал
        send_message(user_id, "🤔 Думаю...")
        answer = ask_gigachat(text)
        if answer is not None:
            send_message(user_id, answer)


# === ЗАПУСК ЛОНГПОЛЛА ===

print(f"✅ Бот запущен. Группа ID: {GROUP_ID}")
print(f"📌 Админ ID: {ADMIN_ID}")
print(f"📌 Модель: {GIGACHAT_MODEL}")
print("⏳ Ожидаю сообщения...\n")

longpoll = VkBotLongPoll(vk_session, group_id=config.GROUP_ID)
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
        handle_message(event)
