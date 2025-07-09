Фудграм [![Main Foodgram workflow](https://github.com/PashaDyakonov/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/PashaDyakonov/foodgram/actions/workflows/main.yml)

Фудграм — это платформа для любителей кулинарии, где можно:
Делиться своими рецептами
Открывать для себя новые рецепты от других пользователей
Сохранять понравившиеся рецепты в избранное
Подписываться на интересных авторов
Зарегистрированные пользователи получают доступ к удобному инструменту "Список покупок", который помогает собрать все необходимые продукты для выбранных рецептов.

Разработчик проекта

Автор проекта — [Павел Дьяконов. GitHub: https://github.com/PashaDyakonov](https://github.com/PashaDyakonov)

В проекте применялись:

- Язык программирования Python
- Фреймворк Django
- Django REST Framework для API
- База данных PostgreSQL
- Серверы Gunicorn и Nginx
- Технологии контейнеризации Docker и Docker Compose
- Docker Volumes для хранения данных
- Docker Hub для хранения образов
- GitHub Actions для автоматизации процессов

Настройка CI/CD

Процесс непрерывной интеграции и доставки настроен с помощью:
- GitHub Actions — для автоматизации рабочих процессов
- Docker — для упаковки приложения в контейнеры
- Конфигурация находится в файле .github/workflows/main.yml

Запуск проекта с помощью Docker

Сделайте клон репозитория:
    
    '''
    git clone https://github.com/PashaDyakonov/foodgram.git
    '''
    

Перейдите в папку с docker-конфигурацией:
    
    cd foodgram/infra
    

Перед запуском создайте файл .env на основе example.env и укажите:
    
    '''
    DB_NAME=имя_вашей_бд
    DB_USER=ваш_пользователь_бд
    DB_PASSWORD=пароль_к_бд
    DB_HOST=db
    DB_PORT=5432
    '''
    

Для запуска контейнера:

    docker-compose up -d

После запуска контейнеров выполните:

    docker-compose exec web python manage.py migrate
    docker-compose exec web python manage.py createsuperuser
    docker-compose exec web python manage.py loaddata initial_data

Сборка статических файлов:

    docker-compose exec web python manage.py collectstatic

Запуск сервера
Проект будет доступен по адресу http://localhost:8000 после выполнения:

    docker-compose up

Альтернативный запуск без Docker
Клонируйте репозиторий:

    git clone https://github.com/PashaDyakonov/foodgram.git

Перейдите в папку проекта:

    cd foodgram/

Создайте и активируйте виртуальное окружение:

    python -m venv venv
    source venv/bin/activate  # Для Linux/Mac
    venv\Scripts\activate    # Для Windows

Создайте .env файл с настройками:

    SECRET_KEY=ваш_секретный_ключ
    DATABASE_URL=строка_подключения_к_бд

Примените миграции и создайте администратора:

    python manage.py migrate
    python manage.py createsuperuser

Импортируйте данные об ингредиентах:

    python manage.py load_ingredients

Запустите сервер:

    python manage.py runserver
