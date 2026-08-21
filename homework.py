import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot

load_dotenv()

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        logging.info(f"Начало отправки сообщения: {message}")
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f"Сообщение успешно отправлено в Telegram: {message}")
    except Exception as error:
        logging.error(f"Ошибка при отправке сообщения в Telegram: {error}")


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    payload = {"from_date": timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        raise Exception(f"Ошибка при запросе к API: {error}")

    if response.status_code != HTTPStatus.OK:
        raise Exception(
            f"Эндпоинт {ENDPOINT} недоступен. Код ответа: {
                response.status_code}")

    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError("Ответ API не является словарем")
    if "homeworks" not in response:
        raise KeyError('В ответе API отсутствует ключ "homeworks"')
    homeworks = response.get("homeworks")

    if not isinstance(homeworks, list):
        raise TypeError('Под ключом "homeworks" пришел не список')
    return homeworks


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе её статус."""
    if "homework_name" not in homework:
        raise KeyError('В словаре homework отсутствует ключ "homework_name"')

    if "status" not in homework:
        raise KeyError('В словаре homework отсутствует ключ "status"')

    homework_name = homework["homework_name"]
    status = homework["status"]

    if status not in HOMEWORK_VERDICTS:
        raise KeyError(f"Неизвестный статус работы: {status}")

    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical("Отсутствуют обязательные переменные окружения!")
        sys.exit("Отсутствуют обязательные переменные окружения!")

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_error_message = ""

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                logging.debug("Статус домашних работ не изменился.")
            timestamp = response.get("current_date", timestamp)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logging.error(message)
            if message != last_error_message:
                send_message(bot, message)
                last_error_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
