# Використовуємо стабільний Python 3.11
FROM python:3.11-slim

# Встановлюємо системні пакети, які потрібні для pydub і Google APIs
RUN apt-get update && apt-get install -y ffmpeg

# Встановлюємо залежності
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код
COPY . .

# Вказуємо команду запуску
CMD ["python", "webhook_main.py"]
