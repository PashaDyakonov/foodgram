Фудграм [![Main Foodgram workflow](https://github.com/PashaDyakonov/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/PashaDyakonov/foodgram/actions/workflows/main.yml)

Фудграм — это платформа для любителей кулинарии, где можно:
Делиться своими рецептами
Открывать для себя новые рецепты от других пользователей
Сохранять понравившиеся рецепты в избранное
Подписываться на интересных авторов
Зарегистрированные пользователи получают доступ к удобному инструменту "Список покупок", который помогает собрать все необходимые продукты для выбранных рецептов.

Разработчик проекта

Автор проекта — [Павел Дьяконов. GitHub](https://github.com/PashaDyakonov)

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

1) Сделайте клон репозитория:
    
    '''
    git clone https://github.com/PashaDyakonov/foodgram.git
    '''
    

2) Перейдите в папку с docker-конфигурацией:
    
    '''
    cd foodgram/infra
    '''

3) Перед запуском создайте файл .env на основе example.env и укажите:
    
    '''
    DB_NAME=имя_вашей_бд
    DB_USER=ваш_пользователь_бд
    DB_PASSWORD=пароль_к_бд
    DB_HOST=db
    DB_PORT=5432
    '''
    
4) Для запуска контейнера:

    '''
    docker-compose up -d
    '''

5) После запуска контейнеров выполните:

    '''
    docker-compose exec web python manage.py migrate
    docker-compose exec web python manage.py createsuperuser
    docker-compose exec web python manage.py loaddata initial_data
    '''

6) Сборка статических файлов:

    '''
    docker-compose exec web python manage.py collectstatic
    '''

Запуск сервера
Проект будет доступен по адресу http://localhost:8000 после выполнения:

    '''
    docker-compose up
    '''

Альтернативный запуск без Docker

1) Клонируйте репозиторий:

    '''
    git clone https://github.com/PashaDyakonov/foodgram.git
    '''

2) Перейдите в папку проекта:

    '''
    cd foodgram/
    '''

3) Создайте и активируйте виртуальное окружение:

    '''
    python -m venv venv
    source venv/bin/activate  # Для Linux/Mac
    venv\Scripts\activate    # Для Windows
    '''

4) Создайте .env файл с настройками:

    '''
    SECRET_KEY=ваш_секретный_ключ
    DATABASE_URL=строка_подключения_к_бд
    '''

5) Примените миграции и создайте администратора:

    '''
    python manage.py migrate
    python manage.py createsuperuser
    '''

6) Импортируйте данные об ингредиентах и тэгах:

    '''
    python manage.py import_ingredients
    python manage.py import_tags
    '''

Запустите сервер:

    '''
    python manage.py runserver
    '''


Основные ссылки:

-  Рабочий сервер: [https://foodgrampc.hopto.org](https://foodgrampc.hopto.org)
-  Админ-панель: [https://foodgrampc.hopto.org/admin](https://foodgrampc.hopto.org/admin)
-  Документация API: [https://foodgrampc.hopto.org/api/docs](https://foodgrampc.hopto.org/api/docs)
-  Docker образ: [https://hub.docker.com/r/vegence/foodgram](https://hub.docker.com/r/vegence/foodgram)
