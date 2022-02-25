import logging
import os

import time
import requests
import telegram
import datetime

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
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
    """"Отправляет в Telegram чат сообщение.

    Ключевые аргументы:
    bot -- экземпляр класса Bot,
    message -- текстовое сообщение - тип str
    """
    return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    """"Возвращает ответ API.

    Ключевые аргументы:
    timestamp -- временная метка - текущее время,
    params -- словарь параметров,
    answer -- ответ, преобразованный из формата JSON к типам данных Python
    """
    params = {'from_date': current_timestamp}

    try:
        homework_statuses = requests.get(ENDPOINT, headers=HEADERS,
                                         params=params)
        answer = homework_statuses.json()
        return answer
    except Exception:
        logging.error('Недоступность эндпоинта.')


def check_response(response):
    """Функция возвращает список домашних работ.

    Ключевые аргументы:
    list_homework -- список домашних работ,
    каждый элемент списка - это словарь с ключами:
    id, status, approved, homework_name, reviewer_comment,
    date_updated, lesson_name"""

    list_homework = response['homeworks']
    if (isinstance(list_homework, list)):
        return list_homework
    else:
        logging.info('Тип данных, полученного ответа,'
                     'не соответвует ожидаемому.')


def parse_status(home):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    Возвращает строку для отправки в Telegram чат"""

    homework_name = home['homework_name']
    homework_status = home['status']

    if homework_status == 'approved':
        verdict = HOMEWORK_STATUSES['approved']
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    elif homework_status == 'reviewing':
        verdict = HOMEWORK_STATUSES['reviewing']
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    elif homework_status == 'rejected':
        verdict = HOMEWORK_STATUSES['rejected']
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logging.error('Недокументированный статус домашней работы,'
                      'обнаруженный в ответе API.')


def check_tokens():
    """Проверяет доступность переменных окружения."""

    if 'PRACTICUM_TOKEN' in os.environ:
        if 'TELEGRAM_TOKEN' in os.environ:
            if 'TELEGRAM_CHAT_ID' in os.environ:
                return True
    else:
        logging.critical('Отсутствие обязательных переменных окружения'
                         'во время запуска бота.')
        return False


def main():
    """Основная логика работы бота.

    Сделать запрос к API.
    Проверить ответ.
    Если есть обновления —
    получить статус работы из обновления и отправить сообщение в Telegram.
    Подождать некоторое время и сделать новый запрос."""

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    #current_timestamp = int(time.time())
    now_datetime = datetime.datetime.now() - datetime.timedelta(30)
    now = int(time.mktime(now_datetime.timetuple()))
    a = now_datetime.timetuple()
    b = time.strftime('%d.%m.%Y %H:%M', a)
    print(b)

    check_variable = check_tokens()

    while check_variable:
        try:
            resp = get_api_answer(now)
            print(resp)
            check_answer = check_response(resp)
            print(check_answer)
            for i in check_answer:
                mess = parse_status(i)
                print(mess)
                send_message(bot, mess)
                logging.info('Удачная отправка сообщения в Telegram.')
            #current_timestamp = int(time.time())
            now = int(time.mktime(now_datetime.timetuple()))

            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            logging.error('Другие сбои при запросе к эндпоинту.')
    else:
        pass


if __name__ == '__main__':
    main()
