# Используйте официальный образ Python
FROM python:3.9-slim

# Установите рабочую директорию
WORKDIR /app

# Копируйте зависимости и установите их
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Копируйте все файлы в рабочую директорию
COPY . .

# Установите переменную окружения для Flask
ENV FLASK_APP=index.py

# Определите команду для запуска приложения
CMD ["flask", "run", "--host=0.0.0.0"]
