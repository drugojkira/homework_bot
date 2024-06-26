# Homework Bot

## Описание
Homework Bot - это бот, который помогает с выполнением домашних заданий. Он написан на Python и использует различные библиотеки для тестирования и управления зависимостями.

## Установка
Для установки и запуска проекта выполните следующие шаги:

1. Клонируйте репозиторий:
    ```bash
    git clone <URL вашего репозитория>
    ```
2. Перейдите в директорию проекта:
    ```bash
    cd homework_bot-master
    ```
3. Установите необходимые зависимости:
    ```bash
    pip install -r requirements.txt
    ```

## Запуск
Для запуска бота используйте команду:
```bash
python homework.py
```

Тестирование
Проект содержит набор тестов, которые можно запустить с помощью pytest. Для этого выполните:

```bash
pytest
```
Структура проекта
```bash
.gitignore - файл, содержащий список файлов и директорий, игнорируемых Git.
Procfile - файл, используемый для декларации процессов, которые должны быть запущены на хостинге (например, Heroku).
README.md - этот файл с описанием проекта.
homework.py - основной файл с кодом бота.
pytest.ini - конфигурационный файл для pytest.
requirements.txt - список зависимостей проекта.
setup.cfg - конфигурационный файл для настройки проекта.
tests/ - директория с тестами:
check_utils.py - вспомогательные функции для тестирования.
conftest.py - файл конфигурации тестов.
test_bot.py - тесты для бота.
fixtures/ - директория с фикстурами:
fixture_data.py - данные для тестирования.
```
