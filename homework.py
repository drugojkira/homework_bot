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

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_FILE = os.path.join(os.path.dirname(__file__), 'logfile.log')


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

if __name__ == "__main__":
    setup_logger()
    logging.info("Logger initialized")


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if not PRACTICUM_TOKEN:
        logging.error('Переменная окружения PRACTICUM_TOKEN отсутствует')
    if not TELEGRAM_TOKEN:
        logging.error('Переменная окружения TELEGRAM_TOKEN отсутствует')
    if not TELEGRAM_CHAT_ID:
        logging.error('Переменная окружения TELEGRAM_CHAT_ID отсутствует')

    return PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID


def send_message(bot, message):
    """Отправляет сообщение через бота в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение отправлено: {}'.format(message))
        logging.debug('Сообщение успешно отправлено в Telegram: {}'.format(message))
    except Exception as e:
        logging.error('Произошла ошибка при отправке сообщения в Telegram: {}'
                      .format(e), exc_info=True)


def get_api_answer(timestamp):
    """Делает запрос к API ЯндексПрактикум."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.exceptions.RequestException as error:
        raise ex.SystemExit(f'{ENDPOINT} с параметрами {params} не доступен: {error}')
    if response.status_code != HTTPStatus.OK:
        raise ex.EndpointAccessError(f'Проблема с доступом к {ENDPOINT}. '
                                     f'Код ответа: {response.status_code}')
    try:
        json_response = response.json()
        if 'code' in json_response or 'error' in json_response:
            error_message = json_response.get('error') or json_response.get('code')
            raise ex.EndpointAccessError(f'Произошла ошибка при запросе к {ENDPOINT}:'
                                         f'{error_message}')
        return json_response
    except decoder.JSONDecodeError as error:
        raise decoder.JSONDecodeError(
            f'Ответ API не преобразуется в JSON: {error}'
        )


def check_response(response): 
    """Возвращает список домашних работ.""" 
    if not isinstance(response, dict):
        raise TypeError('Ответ API должен быть представлен в виде словаря')

    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Данные под ключом "homeworks" не являются списком')

    return homeworks


def parse_status(homework): 
    """Получает статус домашней работы.""" 
    homework_name = homework.get('homework_name') 
    if 'homework_name' not in homework: 
        raise KeyError('Ответ API не содержит ключа "homework_name"') 

    homework_status = homework.get('status') 
    if 'status' not in homework: 
        raise KeyError('Ответ API не содержит ключа "status"') 

    verdict = HOMEWORK_VERDICTS.get(homework_status) 
    if verdict is None: 
        raise ValueError(f'Неизвестный статус "{homework_status}"'
                         f'у работы "{homework_name}"') 

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствуют обязательные переменные окружения.'
                         'Программа продолжает работу.')
        return
    
    last_homework_time = None
    last_message_cache = ''
    bot = TeleBot(token=TELEGRAM_TOKEN)

    while True:
        try:
            response = get_api_answer(last_homework_time)
            homeworks = check_response(response)
            
            if homeworks:
                latest_homework = homeworks[-1]
                message = parse_status(latest_homework)
                if message:
                    send_message(bot, message)
                    last_homework_time = latest_homework['status_updated']
            
            time.sleep(RETRY_PERIOD)
            
        except Exception as error:
            message = f'Произошла ошибка: {error}'
            logging.error(message)
            if message != last_message_cache:
                send_message(bot, message)
                last_message_cache = message
            
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
