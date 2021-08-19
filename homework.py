import json
import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot, error

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename=os.path.join(os.path.dirname(__file__), 'bot.log'),
    filemode='w',
    datefmt='%Y-%m-%d, %H:%M:%S',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(levelname)s, %(message)s'))
logger.addHandler(handler)

try:
    PRAKTIKUM_TOKEN = os.environ.get('PRAKTIKUM_TOKEN')
    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
except KeyError:
    logger.error('Ошибка в переменных токенов')

BOT_CLIENT = Bot(token=TELEGRAM_TOKEN)
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
STATUSES = {
    'reviewing': 'Проект на ревью.',
    'rejected': 'К сожалению, в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, работа зачтена!',
}
time.sleep(300)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in STATUSES:
        logger.error('Ошибка, неизвестный статус')
        raise Exception('Ошибка, неизвестный статус')
    if homework_name is None or homework_status is None:
        logger.error('homework_name is None OR homework_status is None')
        raise Exception('homework_name is None OR homework_status is None')
    return (f'У вас проверили работу "{homework_name} "!'
            f'{STATUSES[homework_status]}')


def get_homeworks(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    params = {'from_date': current_timestamp}

    try:
        homework_statuses = requests.get(
            url=URL,
            headers=HEADERS,
            params=params
        )
    except requests.exceptions.RequestException:
        logger.error('Request exception occurred', exc_info=True)
        send_message('Request exception occurred')
        raise('Ошибка в реквесте при запросе к апи практикума')

    try:
        YP_request = homework_statuses.json()
    except json.decoder.JSONDecodeError:
        logger.error('JSONDecodeError occurred', exc_info=True)
        send_message('JSONDecodeError occurred')
        raise('Ошибка при расшифровке json-файла')
    if 'error' in YP_request:
        logger.error(YP_request['error'])
        send_message(YP_request['error'])
    return YP_request


def send_message(message):
    try:
        return BOT_CLIENT.send_message(chat_id=CHAT_ID, text=message)
    except error.TelegramError:
        raise SystemExit('Ошибка на стороне телеграма')


def main():
    logger.debug('logging is started')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homeworks(current_timestamp)
            if new_homework.get('homeworks'):
                last_hw = new_homework('homeworks')[0]
                send_message((parse_homework_status(last_hw)))
                logger.info('Message was sent')
                current_timestamp = int(time.time())
        except requests.exceptions.RequestException:
            logger.error('Exception occurred', exc_info=True)
            send_message('Exception occurred')
            time.sleep(5)
        except AttributeError:
            logger.error('AttributeError', exc_info=True)
            send_message('AttributeError occurred')
            time.sleep(5)


if __name__ == '__main__':
    main()
