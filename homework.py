import os
import sys
import time
import logging
from json import decoder
from http import HTTPStatus

import requests
from telebot import TeleBot
from dotenv import load_dotenv

import exceptions

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = ('https://practicum.yandex.ru/api/user_api/homework_statuses/')
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': ('Работа проверена: ревьюеру всё понравилось. Ура!'),
    'reviewing': ('Работа взята на проверку ревьюером.'),
    'rejected': ('Работа проверена: у ревьюера есть замечания.')
}


def setup_logger():
    """Установка логгера."""
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'logfile.log')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    token_names = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']

    for token, token_name in zip(tokens, token_names):
        if not token:
            logging.error(f'Переменная окружения {token_name} отсутствует')

    return all(tokens)


def send_message(bot, message):
    """Отправляет сообщение через бота в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        success_message = (
            f'Сообщение успешно отправлено в Telegram: {message}')
        logging.info(success_message)
        logging.debug(success_message)

    except Exception as e:
        error_message = (
            f'Произошла ошибка при отправке сообщения в Telegram: {e}')
        logging.error(error_message, exc_info=True)
        return error_message


def get_api_answer(timestamp):
    """Делает запрос к API ЯндексПрактикум."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as error:
        error_message = (
            f'{ENDPOINT} с параметрами {params} не доступен: {error}')
        raise exceptions.SystemExit(error_message)

    if response.status_code != HTTPStatus.OK:
        error_message = (
            f'Проблема с доступом к {ENDPOINT} с параметрами {params}. '
            f'Код ответа: {response.status_code}')
        raise exceptions.EndpointAccessError(error_message)

    json_response = response.json()
    if 'code' in json_response or 'error' in json_response:
        error_key = None
        error_value = None
        if 'code' in json_response:
            error_key = 'code'
            error_value = json_response.get('code')
        elif 'error' in json_response:
            error_key = 'error'
            error_value = json_response.get('error')
        raise exceptions.EndpointAccessError(
            f'Произошла ошибка при запросе к {ENDPOINT}: {error_value}. '
            f'Параметры запроса: {params}, Ключ: {error_key}, '
            f'Значение: {error_value}')
    return json_response


def check_response(response):
    """Возвращает список домашних работ."""
    if not isinstance(response, dict):
        error_message = 'Ответ API должен быть представлен в виде словаря'
        raise TypeError(error_message.format())

    if 'homeworks' not in response:
        error_message = 'Ответ API не содержит ключа "homeworks"'
        raise KeyError(error_message.format())

    homeworks = response.get('homeworks')

    if not isinstance(homeworks, list):
        error_message = 'Данные под ключом "homeworks" не являются списком'
        raise TypeError(error_message.format())

    return homeworks


def parse_status(homework):
    """Получает статус домашней работы."""
    if 'homework_name' not in homework:
        error_message = 'Ответ API не содержит ключа "homework_name"'
        raise KeyError(error_message.format())

    homework_name = homework.get('homework_name')

    if 'status' not in homework:
        error_message = 'Ответ API не содержит ключа "status"'
        raise KeyError(error_message.format())

    homework_status = homework.get('status')

    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if verdict is None:
        error_message = (
            'Неизвестный статус "{homework_status}" у работы '
            '"{homework_name}"')
        raise ValueError(error_message.format())

    return (
        f'Изменился статус проверки работы "{homework_name}". '
        f'{verdict}')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical(
            'Отсутствуют обязательные переменные окружения.'
            'Программа продолжает работу.')
        return

    last_homework_time = 0  # Первоначальное значение timestamp
    last_message_cache = ''
    bot = TeleBot(token=TELEGRAM_TOKEN)

    while True:
        try:
            response = get_api_answer(last_homework_time)
            homeworks = check_response(response)

            if homeworks:
                latest_homework = max(
                    homeworks,
                    key=lambda x: x.get('status_updated'))
                message = parse_status(latest_homework)
                if message:
                    send_message(bot, message)
                    last_homework_time = latest_homework.get('status_updated')
                    last_message_cache = message

            time.sleep(RETRY_PERIOD)

        except Exception as error:
            message = f'Произошла ошибка: {error}'
            logging.error(message)
            if message != last_message_cache:
                send_message(bot, message)
                last_message_cache = message

            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    setup_logger()
    logging.info("Logger initialized")
