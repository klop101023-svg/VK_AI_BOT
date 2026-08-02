import os
from dotenv import load_dotenv

load_dotenv()

# === ВК ===
VK_TOKEN = os.getenv("VK_TOKEN")
if not VK_TOKEN:
    raise ValueError("❌ VK_TOKEN не задан в .env")

GROUP_ID = os.getenv("GROUP_ID")
if not GROUP_ID:
    raise ValueError("❌ GROUP_ID не задан в .env")

# === AITUNNEL (вместо OpenRouter) ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY не задан в .env")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.aitunnel.ru/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "qwen/qwen3-coder")

# === QWEN PROXY ===
QWEN_PROXY_URL = os.getenv("QWEN_PROXY_URL", "http://localhost:3264")

# === ДОПОЛНИТЕЛЬНО ===
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS if x.strip()]

print("✅ Конфигурация загружена!")
print(f"📌 Модель: {OPENAI_MODEL}")
print(f"📌 API URL: {OPENAI_BASE_URL}")