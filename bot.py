import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import config
# Добавлена библиотека openai (pip install openai)
import openai

# === ПОДКЛЮЧЕНИЕ К VK API ===
vk_session = vk_api.VkApi(token=config.VK_TOKEN)
vk = vk_session.get_api()
print(f"✅ Бот запущен. Группа ID: {config.GROUP_ID}")
print("⏳ Ожидаю сообщения...")

# === ПОДКЛЮЧЕНИЕ К AITUNNEL ===
try:
    # Используйте ваш ключ из личного кабинета AITunnel
    openai.api_key = config.AITUNNEL_API_KEY  
    # Важно: укажите endpoint платформы
    openai.api_base = "https://api.aitunnel.ru/v1"
except Exception as e:
    print(f"❌ Ошибка подключения к AITunnel: {e}")

ADMIN_ID = 1027228715  # Оставим админ‑ID для статистики

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
        print(f"❌ Ошибка отправки сообщения: {e}")

def ask_aitunnel(text):
    """Функция общения с нейросетью через AITunnel"""
    try:
        response = openai.ChatCompletion.create(
            model="gigachat-ultra",
            messages=[
                {"role": "user", "content": text}
            ],
            tools=[{"type": "web_browse"}]  # Включает интернет-поиск
        )
        
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        print(f"❌ Ошибка AITunnel: {e}")
        return None

def handle_message(event):
    user_id = event.object.message['from_id']
    text = event.object.message.get('text', '').strip()  # Удалены лишние пробелы
    print(f"📩 от {user_id}: {text}")

    # Проверка на пустое сообщение
    if not text:
        return

    # Обработка команд
    if text == "/start" or text == "🌿 Главная":
        send_message(user_id, "🌿 Привет! Я Ботаник.\n\n"
                              "🔍 Я ищу актуальную информацию в интернете\n"
                              "💰 Спроси курс доллара\n"
                              "🌤️ Узнай погоду\n"
                              "❓ Задай любой вопрос!")
        return

    if text == "/help" or text == "📋 Команды":
        send_message(user_id, "📋 Команды:\n/start — приветствие\n/stats — твоя статистика\n/clear — очистить историю\n/rules — правила\n/info — информация")
        return

    # Блоки с погодой и курсом доллара можно оставить без изменений
    # ...
    
    # Обычные вопросы -> Нейросеть
    send_message(user_id, "🤔 Думаю...")
    answer = ask_aitunnel(text)
    
    if answer:
        send_message(user_id, answer)
    else:
        send_message(user_id, "⚠️ Ошибка. Попробуй позже.")

def main():
    longpoll = VkBotLongPoll(vk_session, config.GROUP_ID)
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            handle_message(event)

if __name__ == "__main__":
    main()
