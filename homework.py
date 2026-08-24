import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import APIResponseError, JSONDecodeError

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

logger = logging.getLogger(__name__)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = {
        "PRACTICUM_TOKEN": PRACTICUM_TOKEN,
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    }
    return [name for name, val in tokens.items() if not val]


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        logger.info("Начало отправки сообщения: %s", message)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug("Сообщение успешно отправлено в Telegram: %s", message)
    except Exception as error:
        logger.error("Ошибка при отправке сообщения в Telegram: %s", error)


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    payload = {"from_date": timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload,
        )
    except requests.RequestException as error:
        raise APIResponseError(f"Ошибка при запросе к API: {error}")

    if response.status_code != HTTPStatus.OK:
        raise APIResponseError(
            f"Эндпоинт {ENDPOINT} недоступен. "
            f"Код ответа: {response.status_code}"
        )

    try:
        return response.json()
    except Exception as error:
        raise JSONDecodeError(f"Ошибка декодирования JSON: {error}")


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
    if missing_tokens := check_tokens():
        message = (
            "Отсутствуют обязательные переменные окружения: "
            f"{', '.join(missing_tokens)}"
        )
        logger.critical(message)
        sys.exit(message)

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
                logger.debug("Статус домашних работ не изменился.")
            timestamp = response.get("current_date", timestamp)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logger.error("%s", message)
            if message != last_error_message:
                send_message(bot, message)
                last_error_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
