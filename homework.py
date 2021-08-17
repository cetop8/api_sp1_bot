import json
import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

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
    PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
except KeyError:
    logger.error('Ошибка в переменных токенов')

bot_client = Bot(token=TELEGRAM_TOKEN)
headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
time.sleep(300)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = 'unknown_status'
    if homework_name is None or homework_status is None:
        logger.error('homework_name is None OR homework_status is None')
        return (f'{homework_name}: '
                f'homework_name is None OR homework_status is None')
    if verdict == 'unknown_status':
        logger.error('Ошибка, неизвестный статус')
    statuses = {
        'reviewing': 'Проект на ревью.',
        'rejected': 'К сожалению, в работе нашлись ошибки.',
        'approved': 'Ревьюеру всё понравилось, работа зачтена!',
        'unknown_status': 'Ошибка, неизвестный статус'
    }
    return f'У вас проверили работу "{homework_name}"!' \
        f'{statuses[homework_status]}'


def get_homeworks(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    params = {'from_date': current_timestamp}

    try:
        homework_statuses = requests.get(
            url=URL,
            headers=headers,
            params=params
        )
    except requests.exceptions.RequestException:
        logger.error('Request exception occurred', exc_info=True)
        send_message('Request exception occurred', bot_client)
        raise('Ошибка в реквесте при запросе к апи практикума')

    try:
        YP_request = homework_statuses.json()
    except json.decoder.JSONDecodeError:
        logger.error('JSONDecodeError occurred', exc_info=True)
        send_message('JSONDecodeError occurred', bot_client)
        raise('Ошибка при расшифровке json-файла')
    if 'error' in YP_request:
        logger.error(YP_request['error'])
        send_message(YP_request['error'], bot_client)
    return YP_request


def send_message(message):
    try:
        return bot_client.send_message(chat_id=CHAT_ID, text=message)
    except Bot.ResponseError:
        raise('Ошибка на стороне Telegram')


def main():
    logger.debug('logging is started')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homeworks(current_timestamp)
            if new_homework.get('homeworks'):
                last_hw = new_homework('homeworks')[0]
                send_message((parse_homework_status(last_hw)), bot_client)
                logger.info('Message was sent')
            current_timestamp = new_homework('current_date',
                                             current_timestamp)

        except requests.exceptions.RequestException:
            logger.error('Exception occurred', exc_info=True)
            send_message('Exception occurred', bot_client)
            time.sleep(5)
        except AttributeError:
            logger.error('AttributeError', exc_info=True)
            send_message('AttributeError occurred', bot_client)
            time.sleep(5)


if __name__ == '__main__':
    main()
