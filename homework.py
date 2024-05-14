import os
import sys
import time
import logging
from http import HTTPStatus

import requests
from telebot import TeleBot
from dotenv import load_dotenv

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

TOKEN_NAMES = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']

ENV_VAR_MISSING_ERROR = 'Переменная окружения {} отсутствует'
SUCCESS_MESSAGE = 'Сообщение успешно отправлено: {}'
ERROR_MESSAGE = ('Произошла ошибка при отправке сообщения: "{}". Ошибка: {}')
REQUEST_ERROR_MESSAGE = '{} с параметрами {} не доступен: {}'
RESPONSE_STATUS_ERROR_MESSAGE = (
    'Проблема с доступом к {} с параметрами {}. Код ответа: {}'
)
API_ERROR_MESSAGE = (
    'Произошла ошибка при запросе к {}: {}. Параметры запроса: {}, '
    'Ключ: {}, Значение: {}'
)
RESPONSE_NOT_DICT_ERROR = 'Ответ API должен быть представлен в виде словаря,'
'получен тип: {}'
KEY_MISSING_ERROR = 'Ответ API не содержит ключа "homeworks"'
DATA_NOT_LIST_ERROR = (
    'Данные под ключом "homeworks" не являются списком, получен тип: {}'
)
MISSING_KEY_ERROR = 'Ответ API не содержит ключа "{}"'
UNKNOWN_STATUS_ERROR = 'Неизвестный статус "{}" у работы "{}"'
STATUS_CHANGE_MESSAGE = 'Изменился статус проверки работы "{}". {}'
MISSING_ENV_VAR_ERROR = (
    'Отсутствуют обязательные переменные окружения.'
)
GENERIC_ERROR_MESSAGE = 'Произошла ошибка: {}'


def setup_logger():
    """Установка логгера."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler('logfile.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()


def check_tokens():
    """Проверяет доступность переменных окружения и бросает исключение."""
    missing_tokens = [name for name in TOKEN_NAMES if not globals().get(name)]
    if missing_tokens:
        error_message = MISSING_ENV_VAR_ERROR
        logging.critical(error_message)
        raise EnvironmentError(error_message)


def send_message(bot, message):
    """Отправляет сообщение через бота в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        success_message = SUCCESS_MESSAGE.format(message)
        logging.info(success_message)
        logging.debug(success_message)
    except Exception as e:
        error_message = ERROR_MESSAGE.format(message, e)
        logging.error(error_message, exc_info=True)
        return error_message
    return None


def get_api_answer(timestamp):
    """Делает запрос к API ЯндексПрактикум."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as error:
        error_message = REQUEST_ERROR_MESSAGE.format(ENDPOINT, params, error)
        logging.error(error_message)
        raise Exception(error_message)

    if response.status_code != HTTPStatus.OK:
        error_message = RESPONSE_STATUS_ERROR_MESSAGE.format
        (ENDPOINT, params, response.status_code)
        logging.error(error_message)
        raise requests.HTTPError(error_message)

    json_response = response.json()
    for key in ['code', 'error']:
        if key in json_response:
            error_value = json_response.get(key)
            error_message = API_ERROR_MESSAGE.format
            (ENDPOINT, error_value, params, key, error_value)
            logging.error(error_message)
            raise requests.HTTPError(error_message)
    return json_response


def check_response(response):
    """Возвращает список домашних работ."""
    if not isinstance(response, dict):
        raise TypeError(RESPONSE_NOT_DICT_ERROR.format
                        (type(response).__name__))

    if 'homeworks' not in response:
        raise KeyError(KEY_MISSING_ERROR)

    homeworks = response['homeworks']

    if not isinstance(homeworks, list):
        raise TypeError(DATA_NOT_LIST_ERROR.format(type(homeworks).__name__))

    return homeworks


def parse_status(homework):
    """Получает статус домашней работы."""
    if 'homework_name' not in homework:
        raise KeyError(MISSING_KEY_ERROR.format('homework_name'))

    name = homework['homework_name']

    if 'status' not in homework:
        raise KeyError(MISSING_KEY_ERROR.format('status'))

    status = homework['status']

    if status not in HOMEWORK_VERDICTS:
        raise ValueError(UNKNOWN_STATUS_ERROR.format(status, name))

    verdict = HOMEWORK_VERDICTS[status]
    return STATUS_CHANGE_MESSAGE.format(name, verdict)


def main():
    """Основная логика работы бота."""
    last_message_cache = ''
    last_homework_time = 0
    bot = TeleBot(token=TELEGRAM_TOKEN)

    try:
        check_tokens()
    except Exception as error:
        logger.error("Critical token check error: %s", error)
        return

    while True:
        try:
            response = get_api_answer(last_homework_time)
            homeworks = check_response(response)
            if homeworks:
                latest_homework = homeworks[0]
                message = parse_status(latest_homework)
                if message != last_message_cache:
                    error_message = send_message(bot, message)
                    if error_message is None:
                        last_message_cache = message
        except Exception as error:
            logger.error("Error during bot operation: %s", error)
            error_message = GENERIC_ERROR_MESSAGE.format(error)
            if error_message != last_message_cache:
                send_message(bot, error_message)
                last_message_cache = error_message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    setup_logger()
    logger.info("Logger initialized")
    main()
