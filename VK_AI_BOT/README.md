# 🤖 VK AI Bot

Многофункциональный бот для **ВКонтакте**, предоставляющий доступ к различным моделям ИИ, с расширенными возможностями форматирования ответов — включая **рендеринг LaTeX** в PDF и изображения.

Бот выступает в роли **единого интерфейса** для нескольких ИИ-сервисов:

- **Локальный Qwen (прокси)** — модели `qwen3-max` (текст) и `qwen3-vl-plus` (изображения).  
  Поддерживает сохранение контекста диалога (*память*).
- **OpenRouter** — доступ к моделям `kimi` и `deepseek`.

---

## 🚀 Ключевые возможности

- **Поддержка нескольких ИИ:** Переключайтесь между Qwen, Kimi и DeepSeek *на лету*.
- **Анализ изображений (Vision):** Отправьте боту фото (с моделью Qwen) — он проанализирует изображение.
- **Продвинутый рендеринг математики:**
  - Поддерживается режим `/math`, где бот просит ИИ использовать LaTeX.
  - Ответы могут быть отформатированы как:
    - `text` — формулы `\LaTeX` → Unicode (по умолчанию)
    - `image` — весь ответ рендерится в PNG-изображение
    - `pdf` — весь ответ рендерится в PDF-документ

- **Специализированные режимы:**
  - `/math` — решение математических задач (LaTeX)
  - `/code` — написание и анализ кода
  - `/raw` — прямое общение без инструкций

- **Управление контекстом:**  
  Поддержка *памяти* в диалогах при ответе на сообщение и команда `/new` для сброса истории.

- **Контроль доступа:**  
  Возможность ограничить использование бота только для доверенных пользователей (`TRUSTED_IDS`).

---

## 🛠️ Команды

### 🤖 Основные команды

```text
/model qwen|kimi|deepseek   # Выбор модели ИИ
/new                        # Сбросить или начать новый диалог
```

### ⚙️ Режимы (влияют на работу ИИ)

```text
/raw   # 'Сырой' текст
/math  # Для задач и формул (LaTeX, PDF/Image)
/code  # Для программирования и анализа кода
```

### 🧾 Формат вывода (для /math)

```text
/format text|image|pdf
/text   # Текст (по умолчанию для /code и /raw)
/image  # Картинка (с формулами)
/pdf    # Документ (с формулами, по умолчанию для /math)
```

📸 Просто отправьте фото (и текст) — Qwen его проанализирует!

---

## ⚙️ Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/Baillora/VK_AI_BOT
cd VK_AI_BOT
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
# Для Linux / macOS
source venv/bin/activate
# Для Windows (cmd.exe)
venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка локального API-прокси для Qwen (обязательно для Qwen)

Для работы моделей `qwen3-max` и `qwen3-vl-plus` требуется запущенный API-прокси.  
Рекомендуется использовать **[FreeQwenApi by y13sint](https://github.com/y13sint/FreeQwenApi)**:


По умолчанию прокси доступен по адресу `http://localhost:3264`.

---

### 5. Создание файла `.env`

В корне проекта создайте файл `.env` и укажите параметры:

```env
# Токен вашего сообщества VK (с правами "messages")
VK_TOKEN="vk1.a.EXAMPLE..."

# ID вашего сообщества (только цифры)
GROUP_ID="123456789"

# Ключ API от OpenRouter.ai
OPENROUTER_API_KEY="sk-or-v1-EXAMPLE..."

# URL локального прокси Qwen
QWEN_PROXY_URL="http://localhost:3264"

# (Опционально) Список доверенных пользователей (через запятую)
TRUSTED_USER_IDS="12345,67890"

# (Опционально) Данные для идентификации в OpenRouter
APP_REFERER="https://my-vk-bot.com"
APP_TITLE="My VK AI Bot"
```

> **Примечание:** убедитесь, что `VK_TOKEN` имеет права на работу с `messages` у сообщества.

---

### 6. Запуск бота

```bash
python bot.py
```

или на Windows:

```bat
start.bat
```

---

## 📦 Зависимости

| Библиотека        | Назначение                                    |
|-------------------|-----------------------------------------------|
| `vk_api`          | Взаимодействие с API ВКонтакте                |
| `python-dotenv`   | Загрузка переменных окружения из `.env`       |
| `openai`          | Клиент для OpenRouter API                     |
| `requests`        | Запросы к локальному прокси Qwen              |
| `Pillow`          | Создание изображений с ответами               |
| `reportlab`       | Генерация PDF-документов с ответами           |

---

## 🧩 Примеры использования

**Пример 1. Решение математической задачи в PDF**

```text
/model qwen
/math
/format pdf
Решите интеграл ∫_0^1 x^2 dx и выведите решение в LaTeX.
```

**Пример 2. Анализ изображения (Qwen Vision)**

1. Отправьте изображение в чат бота.  
2. Добавьте подпись:
   
   ```text
   Что изображено на фото?
   ```
4. Модель `qwen3-vl-plus` выполнит визуальный анализ и вернёт ответ.

---

## 🔒 Контроль доступа

Если вы хотите ограничить доступ к боту, заполните переменную `TRUSTED_USER_IDS` в `.env` списком VK ID через запятую.  
Если `TRUSTED_USER_IDS` пустая — бот отвечает всем пользователям.

---

## ℹ️ Полезные советы

- Для корректной работы рендеринга формул используйте режим `/math`.
- Формат `pdf` лучше подходит для длинных математических решений.
- Для анализа изображений используйте `qwen3-vl-plus` через локальный прокси.

---

## 📄 License

Этот проект лицензирован под **MIT license**. Смотрите [`ЛИЦЕНЗИЮ`](./LICENSE) для большей информации.

---

## ✉️ Контакты / Issues

Если что-то работает некорректно — создайте issue в репозитории и приложите лог или описание шагов воспроизведения.

---

## Авторы

- [@Baillora](https://github.com/Baillora)

---

[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](https://choosealicense.com/licenses/mit/)
[![Release](https://img.shields.io/github/v/release/Baillora/VK_AI_BOT?style=for-the-badge&logo=github&label=Release&color=blue)](https://github.com/Baillora/VK_AI_BOT/releases)
[![Python Versions](https://img.shields.io/badge/Python-3.8%20%7C%203.9%20%7C%203.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-API-7C4DFF?style=for-the-badge&logo=openai&logoColor=white)](https://openrouter.ai/)
[![VK API](https://img.shields.io/badge/VK-API-4A76A8?style=for-the-badge&logo=vk&logoColor=white)](https://dev.vk.com/)

[![Status](https://img.shields.io/badge/Status-Active%20Development-2ECC71?style=for-the-badge&logo=githubactions&logoColor=white)](#)
[![Last Commit](https://img.shields.io/github/last-commit/Baillora/VK_AI_BOT?style=for-the-badge&logo=git&logoColor=white&label=Last%20Commit)](#)
