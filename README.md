# journal_final

Социальная сеть для публикации дневник дневникоав
Здесь пользаватель имеет возможности:
- публиковать посты с картинками, 
- просматривать посты других пользователей,
- подписыватся на авторов и просматривать из записи.
Просмотр записей может осуществлятьлюбойользователь, а публиковать посты, может только авторизованый пользователь.

## рачиваем проект:

Клонируем репозиторий на локашьную машину;
переходим в папку проекта в консоли:
```
cd hw05_final
```
Cоздать и активировать виртуальное окружение:

```
python -m venv env
```

```
source venv/Scripts/activate
```

```
python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python manage.py migrate
```
Выполнить загрузку информации в базу данных:

```
python manage.py fill_database
```

Запустить проект:

```
python manage.py runserver
```

## Системные требования
Требования соответствуют Django 2.2.16

## Зависимости
```
Django==2.2.16
mixer==7.1.2
Pillow
pytest==6.2.4
pytest-django==4.4.0
pytest-pythonpath==0.7.3
requests==2.26.0
six==1.16.0
sorl-thumbnail==12.7.0
Faker==12.0.1
django-debug-toolbar==3.2.4
```
размещены в файле requirements.txt

## Инструменты разработки
Основной инструмент - Django,
Дополнительные инструменты: Pillow 


## Развитие проекта
Планируется добавить возможность, отправлять личные сообщения (мессенджер).
идет разработка...

[![CI](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/yandex-praktikum/hw05_final/actions/workflows/python-app.yml)
