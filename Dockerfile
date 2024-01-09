# Используйте официальный образ Python с Alpine Linux для легковесности
FROM python:3.10-alpine

# Установите рабочую директорию в контейнере
WORKDIR /app

# Установите зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируйте остальные файлы проекта в контейнер
COPY . .

# Объявите порт, который будет слушать приложение
EXPOSE 8000

# Запустите сервер разработки Django
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "Simple_solutions.wsgi:application"]
