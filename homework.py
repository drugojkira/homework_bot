import os
import time
import logging
from json import decoder
from http import HTTPStatus

import requests
from telebot import TeleBot
from dotenv import load_dotenv

import exceptions as ex

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID


def send_message(bot, message):
    """Отправляет сообщение через бота в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'Сообщение отправлено: {message}')
        logging.debug(f'Сообщение успешно отправлено в Telegram: {message}')
    except ex.TelegramError as error:
        logging.info(f'Сбой при отправке сообщения: {error}')
    except ex.SendMessageError as error:
        logging.info(f'Сбой при отправке сообщения: {error}')
    except Exception as e:
        logging.error(f'Произошла ошибка при отправке сообщения в Telegram:'
                      f'{e}')


def get_api_answer(timestamp):
    """Делает запрос к API ЯндексПрактикум."""
    timestamp = timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as error:
        raise ex.CustomSystemExit(f'Эндпоинт не доступен: {error}')
    if response.status_code != HTTPStatus.OK:
        raise ex.EndpointAccessError(f'Проблема с доступом к {ENDPOINT}. '
                                     f'Код ответа: {response.status_code}')
    try:
        return response.json()
    except decoder.JSONDecodeError as error:
        raise decoder.JSONDecodeError(
            f'Ответ API не преобразуется в JSON: {error}'
        )


def check_response(response):
    """Возвращает список домашних работ."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        raise ex.KeyError('Ответ API не содержит ключа "homeworks"')

    if not isinstance(homeworks, list):
        raise TypeError('Данные под ключом "homeworks" не являются списком')
    elif len(homeworks) == 0:
        raise ex.HomeworksEmptyError('В настоящее время на проверке нет '
                                     'ни одной домашней работы.')

    return homeworks


def parse_status(homework):
    """Получает статус домашней работы."""
    homework_status_cache = {}
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise ex.KeyError('Ответ API не содержит ключа "homework_name"')
    homework_status = homework.get('status')
    if homework_status is None:
        raise ex.KeyError('Ответ API не содержит ключа "homework_status"')
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if verdict is None:
        raise ex.UnknownStatusError(f'Неизвестный статус "{homework_status}" '
                                    f'у работы "{homework_name}"')
    if homework_status != homework_status_cache.get(homework_name):
        homework_status_cache[homework_name] = homework_status
        return (f'Изменился статус проверки работы "{homework_name}". '
                f'{verdict}')
    logging.debug(f'Статус работы "{homework_name}" не изменился')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствуют обязательные переменные окружения. '
                         'Программа продолжает работу.')
        return
    last_message_cache = ''
    bot = TeleBot(token=TELEGRAM_TOKEN)
    send_message(bot, '--- Бот запущен ---')
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                message = parse_status(homework)
                if message:
                    send_message(bot, message)
            current_timestamp = int(time.time())
            time.sleep(RETRY_PERIOD)
        except Exception as error:
            message = f'{error}'
            logging.error(message)
            if message != last_message_cache:
                send_message(bot, message)
                last_message_cache = message
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
