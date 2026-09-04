from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

# === ТВОЙ КЛЮЧ ===
API_KEY = "MDFhMDZkM2EtNGI1MS03NzY4LThiZmUtNDc1YTA2ZTRkNzEwOjA2ZTk2MGY5LTFiZDEtNDgyYy05OWFhLTVkMTVjYWY0MjRkNg=="

try:
    client = GigaChat(
        base_url="https://api.giga.chat/v2",
        credentials=API_KEY,
        scope="GIGACHAT_API_PERS",
        verify_ssl_certs=False,
    )
    print("✅ GigaChat подключён")
    
    messages = [Messages(role=MessagesRole.USER, content="Привет! Как дела?")]
    chat = Chat(model="GigaChat-3-Ultra", messages=messages)
    response = client.chat(chat)
    
    print("✅ Ответ:", response.choices[0].message.content)
    
except Exception as e:
    print("❌ Ошибка:", e)
