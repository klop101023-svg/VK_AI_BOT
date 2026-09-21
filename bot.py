import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
# Библиотека openai совместима с протоколом AITunnel
import openai  # pip install openai
import os  # Для работы с переменными окружения

ADMIN_ID = 1027228715  # Оставим админ‑ID (можно убрать)

# === ПОДКЛЮЧЕНИЕ К VK API через переменные окружения ===
vk_session = vk_api.VkApi(token=os.getenv("VK_TOKEN"))
vk = vk_session.get_api()
print(f"✅ Бот запущен. Группа ID: {os.getenv('GROUP_ID')}")
print("⏳ Ожидаю сообщения...")

# === ПОДКЛЮЧЕНИЕ К AITUNNEL / Нейросеть + Поиск ===
try:
    # Используйте ваш ключ из личного кабинета aitunnel.ru
    openai.api_key = os.getenv("AITUNNEL_API_KEY")  
    # Важно: укажите endpoint платформы
    openai.api_base = "https://api.aitunnel.ru/v1"
except Exception as e:
    print(f"❌ Ошибка подключения к AITunnel: {e}")

def send_message(user_id, text, keyboard=None):
    try:
        vk.messages.send(
            user_id=user_id,
            message=text,
            keyboard=keyboard if keyboard else None,
            random_id=get_random_id(),
        )
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")

def ask_aitunnel(text):
    """Функция общения с нейросетью через AITunnel"""
    try:
        response = openai.ChatCompletion.create(
            model="gigachat-ultra",  # Или gigachat-2-ultra
            messages=[
                {"role": "user", "content": text}
            ],
            tools=[{"type": "web_browse"}],  # Включает интернет-поиск
            tool_choice="auto",  # Платные аккаунты могут использовать авто-выбор инструментов
        )
        
        answer = response.choices[0].message.get("content")
        if not isinstance(answer, str) or len(answer.strip()) == 0:
            return "🤔 Кажется, я задумался слишком глубоко..."
    
        return answer.strip()  # Возвращаем очищенный текст ответа
    
    except Exception as e:
        print(f"❌ Ошибка AITunnel: {e}")
        return f"Ой! Что-то пошло не так: {str(e)}"

def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '').strip()  # Удалены лишние пробелы
    print(f"📩 от {user_id}: {text}")

    # Проверка на пустое сообщение
    if not text:
        return

    # Обработка команд
    if text in ["/start", "/help"]:
        send_message(user_id, "🌿 Привет! Я — бот‑ботаник.\n\n"
                              "🔍 Я ищу актуальную информацию в интернете,\n"
                              "💰 Спроси курс доллара,\n"
                              "🌤️ Узнай погоду,\n"
                              "📜 Задай любой вопрос!")
        return

    # Обычные вопросы -> Нейросеть
    send_message(user_id, "🤔 Думаю...")
    answer = ask_aitunnel(text)
    send_message(user_id, answer)

def main():
    longpoll = VkBotLongPoll(vk_session, int(os.getenv('GROUP_ID')))
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            handle_message(event)

if __name__ == "__main__":
    main()
