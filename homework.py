import logging
import os

import time
import datetime
import requests
import telegram

from dotenv import load_dotenv
from http import HTTPStatus

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

MANDATORY_ENV_VARS = ["PRACTICUM_TOKEN", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID"]

RETRY_TIME = 6
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filemode='w'
)


def send_message(bot, message):
    """Отправляет в Telegram чат сообщение.

    Ключевые аргументы:
    bot -- экземпляр класса Bot,
    message -- текстовое сообщение - тип str
    """
    try:
        return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception:
        logging.error('Cбой при отправке сообщения в Telegram.')


def get_api_answer(current_timestamp):
    """Возвращает ответ API.

    Ключевые аргументы:
    current_timestamp -- временная метка - текущее время,
    params -- словарь параметров,
    answer -- ответ, преобразованный из формата JSON к типам данных Python
    """
    params = {'from_date': current_timestamp}

    homework_statuses = requests.get(ENDPOINT, headers=HEADERS,
                                     params=params)
    if homework_statuses.status_code == HTTPStatus.OK:
        answer = homework_statuses.json()
        homework_statuses.status_code
        return answer
    else:
        logging.error('API возвращает код, отличный от 200.')
        raise ValueError


def check_response(response):
    """Функция возвращает список домашних работ.

    Ключевые аргументы:
    list_homework -- список домашних работ,
    каждый элемент списка - это словарь с ключами:
    id, status, approved, homework_name, reviewer_comment,
    date_updated, lesson_name
    """
    if response:
        if 'homeworks' in response:
            list_homework = response['homeworks']
            if (isinstance(list_homework, list)):
                return list_homework
            else:
                logging.error('Тип данных, полученного ответа,'
                              'имеет некорректный тип.')
                raise AttributeError
        else:
            logging.error('Ответ API не содержит ключа "homeworks".')
            raise KeyError
    else:
        logging.error('Ответ API содержит пустой словарь.')
        raise ValueError


def parse_status(home):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    Возвращает строку для отправки в Telegram чат
    """
    homework_name = home['homework_name']
    homework_status = home['status']

    if homework_status in HOMEWORK_STATUSES:
        if homework_status == 'approved':
            verdict = HOMEWORK_STATUSES[homework_status]
            return (f'Изменился статус проверки '
                    f'работы "{homework_name}". {verdict}')
        elif homework_status == 'reviewing':
            verdict = HOMEWORK_STATUSES[homework_status]
            return (f'Изменился статус проверки '
                    f'работы "{homework_name}". {verdict}')
        else:
            homework_status == 'rejected'
            verdict = HOMEWORK_STATUSES[homework_status]
            return (f'Изменился статус проверки '
                    f'работы "{homework_name}". {verdict}')
    else:
        logging.error('Недокументированный статус'
                      'домашней работы в ответе API.')
        raise KeyError


def check_tokens():
    """Проверяет доступность переменных окружения."""
    try:
        if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            return True
        else:
            return False
    except Exception:
        logging.info('Отсутствуют необходимые переменные окружения.')
        raise PermissionError


def main():
    """Основная логика работы бота.

    1.Сделать запрос к API.
    2.Проверить ответ.
    3.Если есть обновления —
    получить статус работы из обновления и отправить сообщение в Telegram.
    4.Подождать некоторое время и сделать новый запрос.

    """
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    check_variable = check_tokens()
    now_datetime = datetime.datetime.now() - datetime.timedelta(30)
    now = int(time.mktime(now_datetime.timetuple()))

    while check_variable:
        try:
            resp = get_api_answer(now)
            print(resp)
            if len(resp['homeworks']) != 0:
                check_answer = check_response(resp)
                for i in check_answer:
                    mess = parse_status(i)
                    send_message(bot, mess)
                    logging.info('Удачная отправка сообщения в Telegram.')
                now = int(time.mktime(now_datetime.timetuple()))
                time.sleep(RETRY_TIME)
            else:
                logging.info('Отсутствие в ответе новых статусов.')
        except Exception as e:
            message = f'Сбой в работе программы: {e}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
            continue
        else:
            logging.info('Код выполнен без ошибок.')


if __name__ == '__main__':
    main()
