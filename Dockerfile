# Используем базовый образ Python 3.11.10 slim
FROM python:3.11.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл requirements.txt в контейнер
COPY requirements.txt .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё содержимое текущей директории в контейнер
COPY . .

# Запускаем ваш Telegram бот
CMD ["python", "main.py"]

