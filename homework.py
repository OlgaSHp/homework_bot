"""
Telegram-бот обращается к API сервиса Практикум.Домашка.

Узнаёт статус домашней работы и присылает сообщение.

Ошибки логгирует.
"""

import http
import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from telegram.error import TelegramError

from exceptions import (
    DataTypeError, EndpointFailure, GlobalVariableError,
    HttpStatusOkResponseError, MessageDeliveryError,
    MissingErrorInformationAndNonOkStatus, ServiceFailure,
    APIConnectionError
)

load_dotenv()


PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}
TOKEN_NAMES = ("PRACTICUM_TOKEN", "TELEGRAM_TOKEN",
               "TELEGRAM_CHAT_ID", "ENDPOINT")

HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def send_message(bot, message):
    """Отправляет сообщение пользователю в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except TelegramError as error:
        logging.exception(
            f"Ошибка отправки сообщения в Telegram: {error}. "
            f"Сообщение: {message}"
        )
        raise MessageDeliveryError(f"{error}, {message}",
                                   http.HTTPStatus.INTERNAL_SERVER_ERROR)
    logging.debug(f'Сообщение "{message}" отослано', exc_info=True)


def get_api_answer(current_timestamp):
    """Отправка запроса к эндпойнту с параметром временной метки."""
    # Текущая метка времени
    timestamp = current_timestamp or int(time.time())
    time_params = {"from_date": timestamp}
    # Словарь с параметрами запроса
    request_params = {
        "url": ENDPOINT,
        "headers": HEADERS,
        "params": time_params,
    }
    try:
        # Запрос к API
        response = requests.get(**request_params)
    except requests.exceptions.RequestException as error:
        raise APIConnectionError(
            f"{error}, url={ENDPOINT}",
            f"headers={HEADERS}",
            f"params={time_params}",
            http.HTTPStatus.SERVICE_UNAVAILABLE
        )
    response_status = response.status_code
    if response_status != http.HTTPStatus.OK:
        error_msg = (
            f"Ошибка доступа к эндпойнту: статус {response_status}\n"
            f"URL: {ENDPOINT}\n"
            f"Headers: {HEADERS}\n"
            f"Params: {time_params}\n"
        )
        raise EndpointFailure(error_msg)
    # Проверка на наличие ошибки при получение ответа с сервера
    response_json = response.json()
    # Обращаемся к ключам response_json и приводим их к типу set
    if set(response_json.keys()) == {'error', 'code'}:
        error_msg = f"Ошибка {response_json['code']}: {response_json['error']}"
        raise HttpStatusOkResponseError(
            error_msg, http.HTTPStatus.INTERNAL_SERVER_ERROR
            )
    elif response.status_code != http.HTTPStatus.OK:
        raise MissingErrorInformationAndNonOkStatus(
            'Ошибок нет, получен статус ответа,'
            'отличный от HTTPStatus.OK', http.HTTPStatus.BAD_REQUEST
            )
    return response_json


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError(
            "Структура данных ответа API не соответствует требованию: "
            "ожидается словарь."
        )
    # Если ключ 'code' содержится в полученных данных,
    # выдать ошибку доступа к эндпойнту
    if "code" in response:
        code = response.get("code")
        raise ServiceFailure(
            f"{code}", http.HTTPStatus.INTERNAL_SERVER_ERROR
        )
    if not isinstance(response.get("homeworks"), list):
        raise TypeError("Данные не в виде списка")
    # Если ключ 'homeworks' содержится в полученных данных,
    # вернуть первый элемент списка
    if response["homeworks"]:
        return response["homeworks"][0]
    raise IndexError("Пустой список")


def parse_status(homework):
    """Извлекает из информации о домашней работе статус этой работы."""
    if not isinstance(homework, dict):
        raise DataTypeError(f"Неверный тип данных {type}, вместо словаря",
                            http.HTTPStatus.BAD_REQUEST)

    if "homework_name" not in homework:
        raise KeyError("Ответ API не содержит ключ 'homework_name'.")

    homework_name = homework.get("homework_name")
    homework_status = homework.get("status")

    if homework_status not in HOMEWORK_VERDICTS:
        raise NameError(f"{homework_status}")
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    for name in TOKEN_NAMES:
        if not globals()[name]:
            logging.critical(f"Глобальная переменная {name} отсутствует")
            return False
    return True


def main():
    """Основная логика работы программы."""
    if not check_tokens():
        raise GlobalVariableError("Ошибка глобальной переменной",
                                  http.HTTPStatus.INTERNAL_SERVER_ERROR)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            logging.info(homework)
            current_timestamp = response.get("current_date")
        except IndexError:
            message = "Статус работы не изменился"
            send_message(bot, message)
            logging.info(message)
        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)
        logging.info(f"Сообщение {message} отправлено")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s, %(levelname)s, %(message)s, %(lineno)d, %(name)s",
        encoding="utf-8",
        filemode="w",
        filename="homework.log",
        level=logging.INFO,
    )
    main()
