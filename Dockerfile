FROM python:3.11-slim-bullseye

# Создаём рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Монтируем папку данных для статистики
VOLUME [ "/data" ]

# Указываем команду старта
CMD ["python", "bot.py"]
