import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import config
# import requests # Не используется сейчас
import json
import os
from datetime import datetime
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

# === ПОДКЛЮЧЕНИЕ К ВК ===
vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()

# === ПОДКЛЮЧЕНИЕ К GIGACHAT ===
try:
    client = GigaChat(
        base_url="https://api.giga.chat/v2",
        credentials=config.GIGACHAT_CREDENTIALS,
        scope=config.GIGACHAT_SCOPE,
        verify_ssl_certs=False,
    )
    print("✅ GigaChat подключён")
except Exception as e:
    print(f"❌ Ошибка GigaChat: {e}")
    client = None

# СТАТИСТИКА УДАЛЕНА ИЛИ ЗАКОММЕНТИРОВАНА ДЛЯ РАБОТЫ НА ОБЛАЧНЫХ ПЛАТФОРМАХ
# STATS_FILE = "/data/stats.json"
# ADMIN_ID = 1027228715

# def load_stats():
#     if not os.path.exists(STATS_FILE):
#         return {}
#     try:
#         with open(STATS_FILE, "r", encoding="utf-8") as f:
#             return json.load(f)
#     except:
#         return {}
#
# def save_stats(stats):
#     with open(STATS_FILE, "w", encoding="utf-8") as f:
#         json.dump(stats, f, ensure_ascii=False, indent=2)
#
# def update_stats(user_id):
#     stats = load_stats()
#     user_id_str = str(user_id)
#     now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     
#     if user_id_str not in stats:
#         stats[user_id_str] = {
#             "first_seen": now,
#             "last_seen": now,
#             "messages": 0
#         }
#     else:
#         stats[user_id_str]["last_seen"] = now
#     
#     stats[user_id_str]["messages"] += 1
#     save_stats(stats)

def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("🌿 Главная", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("📋 Команды", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📊 Статистика", color=VkKeyboardColor.PRIMARY) # Можно убрать эту кнопку
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

# Функции получения курса доллара и погоды можно оставить как есть
# ...

def ask_gigachat(text):
    """Функция отправки запроса к нейросети с ограничением области поиска"""
    if client is None:
        return "❌ GigaChat не подключён"
    
    try:
        messages = [Messages(role=MessagesRole.USER, content=text)]
        
        # Ограничение поиска только новостями (наиболее стабильный вариант)
        chat = Chat(
            model="GigaChat-3-Ultra",
            messages=messages,
            tools=[{"type": "web_search", "query_modifiers": ["news"]}]
        )
        
        # Альтернатива: поиск по конкретным сайтам
        # chat = Chat(
        #     model="GigaChat-3-Ultra",
        #     messages=messages,
        #     tools=[
        #         {"type": "web_search", 
        #          "query_modifiers": ["site:tass.ru OR site:rbc.ru"]}
        #     ]
        # )

        response = client.chat(chat)
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Ошибка GigaChat: {e}")
        return None

def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '').strip() # Удалены лишние пробелы
    print(f"📩 от {user_id}: {text}")

    # Проверка на пустое сообщение
    if not text:
        return

    # КОММЕНТАРИЙ: Статистика удалена из-за ошибки доступа к файлу
    # update_stats(user_id)

    # ... остальной ваш код обработки сообщений остаётся без изменений
