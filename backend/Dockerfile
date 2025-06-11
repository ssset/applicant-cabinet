# Базовый образ Python
FROM python:3.11-slim

# Установка системных зависимостей, включая Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    libtesseract-dev \
    postgresql-client \
    libpq-dev \
    gcc \
    postgresql-server-dev-15 \
    curl \
    iputils-ping \
    telnet \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Создание директории для логов
RUN mkdir -p /var/log/app && chmod -R 755 /var/log/app

# Установка переменной окружения для Tesseract
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/

# Установка рабочей директории
WORKDIR /app

# Копирование зависимостей
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода бэкенда
COPY backend/ .

# Сбор статических файлов
RUN python manage.py collectstatic --noinput

# Команда для запуска приложения
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "applicant.wsgi:application"]