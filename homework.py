import json
import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logging.basicConfig(
    level=logging.DEBUG,
    filename='bot.log',
    filemode='w',
    datefmt='%Y-%m-%d, %H:%M:%S',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(levelname)s, %(message)s'))
logger.addHandler(handler)

bot_client = Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = 'unknown_status'
    if homework_name is None or homework_status is None:
        logger.error('homework_name is None OR homework_status is None')
        return (f'{homework_name}: '
                f'homework_name is None OR homework_status is None')
    elif homework_status == 'reviewing':
        verdict = 'Проект на ревью.'
    elif homework_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework_status == 'approved':
        verdict = ('Ревьюеру всё понравилось, работа зачтена!')
    elif verdict == 'unknown_status':
        logger.error('Ошибка, неизвестный статус')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

    try:
        homework_statuses = requests.get(
            url=URL,
            headers=headers,
            params=params
        )
    except requests.exceptions.RequestException:
        logger.error('Request exception occurred', exc_info=True)
        send_message('Request exception occurred', bot_client)
        return {}

    try:
        YP_request = homework_statuses.json()
    except json.decoder.JSONDecodeError:
        logger.error('JSONDecodeError occurred', exc_info=True)
        send_message('JSONDecodeError occurred', bot_client)
        return {}
    if 'error' in YP_request:
        logger.error(YP_request['error'])
        send_message(YP_request['error'], bot_client)
    return YP_request


def send_message(message):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    logger.debug('logging is started')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homeworks(current_timestamp)
            if new_homework.get('homeworks'):
                last_hw = new_homework.get('homeworks')[0]
                send_message((parse_homework_status(last_hw)), bot_client)
                logger.info('Message was sent')
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(300)

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
