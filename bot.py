import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
# Библиотека openai совместима с протоколом AITunnel
import openai  # pip install openai
import os  # Для работы с переменными окружения

ADMIN_ID = 1027228715  # Оставим админ‑ID (можно убрать)

# === ПОДКЛЮЧЕНИЕ К VK API через переменные окружения ===
vk_session = vk_api.VkApi(token=os.getenv("VK_TOKEN"))
vk = vk_session.get_api()
print(f"✅ Бот запущен. Группа ID: {os.getenv('GROUP_ID')}")
print("⏳ Ожидаю сообщения...")

# === НАСТРОЙКИ ПОИСКА ===
# ❗️ Измени это значение, если хочешь ограничить область поиска!
SEARCH_MODIFIER = "news"
# Возможные варианты:
# - news — любые новости
# - site:tass.ru — только сайт ТАСС
# - site:cbr.ru — только ЦБ РФ
# - "" (пустая строка) — без ограничений


# === ПОДКЛЮЧЕНИЕ К AITUNNEL / Нейросеть + Поиск ===
try:
    # Проверка наличия ключа напрямую из окружения
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or len(api_key) < 40:
        print(f"❌ Ошибка: Ключ AITunnel не найден или неверен!")
        raise ValueError("API Key is missing or invalid!")
    
    # Указываем endpoint платформы вручную
    openai.api_base = "https://api.aitunnel.ru/v1"
except Exception as e:
    print(f"❌ Ошибка при подключении к AITunnel: {e}")

def send_message(user_id, text):
    try:
        vk.messages.send(
            user_id=user_id,
            message=text,
            random_id=get_random_id(),
        )
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {str(e)}")

def ask_aitunnel(text):
    """Функция общения с нейросетью через AITunnel"""
    # ❗️ Подсказка для поиска: добавляем модификатор области прямо в запрос!
    query_text = f"{text} [{SEARCH_MODIFIER}]"

    # ❗️ ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА ДО ЗАПРОСА!
    # Это решает проблему ошибок на простых вопросах без поиска
    api_key = os.getenv("OPENAI_API_KEY") 
    if not api_key or len(api_key) < 40:
        return "🤔 Кажется, я задумался слишком глубоко..."

    try:
        response = openai.ChatCompletion.create(
            model="gigachat-2-pro",
            messages=[
                {"role": "user", "content": query_text}
            ],
            tools=[{"type": "web_browse"}],  # Включает поиск
            tool_choice="auto",                 # Платные аккаунты могут использовать авто-выбор инструментов
        )
        
        answer = response.choices[0].message.get("content")
        # ❗️ Возвращаем только валидный текстовый ответ
        return answer.strip() if isinstance(answer, str) and len(answer.strip()) > 0 else None
    
    except Exception as e:
        print(f"❌ Ошибка AITunnel: {str(e)}")
        # Функция больше не отправляет ошибку пользователю — это делает основной цикл
        return None

def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '').strip()
    print(f"📩 от {user_id}: {text}")

    # Проверка на пустое сообщение
    if not text:
        return

    # Обработка команд
    if text in ["/start", "/help"]:
        send_message(user_id, "🌿 Привет! Я — бот‑ботаник.\n\n"
                              "🔍 Задай любой вопрос!")
        return

    # Обычные вопросы -> Нейросеть
    send_message(user_id, "🤔 Думаю...")
    answer = ask_aitunnel(text)
    
    # ❗️ Новая проверка: проверяем именно наличие текста в ответе
    # Если ответа нет (например, ошибка), пользователь просто увидит «Думаю...»
    if answer:
        send_message(user_id, answer)

def main():
    longpoll = VkBotLongPoll(vk_session, int(os.getenv('GROUP_ID')))
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            handle_message(event)

if __name__ == "__main__":
    main()
