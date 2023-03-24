"""Кастомные классы ошибок."""


class BaseError(Exception):
    """Базовый класс-исключение."""

    def __init__(self, msg, code):
        """
        msg: Сообщение об ошибке.

        code: HTTP статус ошибки.
        """
        self.msg = msg
        self.code = code


class MessageDeliveryError(BaseError):
    """Ошибка при отправки сообщения."""

    pass


class ServiceFailure(BaseError):
    """Ошибка доступа к определенному эндпойнту."""

    pass


class DataTypeError(BaseError):
    """Ошибка, если тип данных не словарь."""

    pass


class EndpointFailure(Exception):
    """Ошибка, если эндпоинт неправильный или не существует."""

    pass


class GlobalVariableError(BaseError):
    """Ошибка, если глобальная переменная пуста или не отсутствует."""

    pass


class HttpStatusOkResponseError(BaseError):
    """Ошибка, если HTTP-ответ не 200."""

    pass


class MissingErrorInformationAndNonOkStatus(BaseError):
    """Информации об ошибке нет, но статус всё равно не 200."""

    pass


class APIConnectionError(BaseError):
    """Ошибка связи с API."""

    pass
