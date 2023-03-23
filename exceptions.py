"""Кастомные классы ошибок."""


class MessageDeliveryError(Exception):
    """Ошибка при отправки сообщения."""

    pass


class ServiceFailure(Exception):
    """Ошибка доступа к определенному эндпойнту."""

    pass


class DataTypeError(Exception):
    """Ошибка, если тип данных не словарь."""

    pass


class EndpointFailure(Exception):
    """Ошибка, если эндпоинт неправильный или не существует."""

    pass


class ResponseFormatError(Exception):
    """Ошибка, если формат ответа не JSON."""

    pass


class GlobalVariableError(Exception):
    """Ошибка, если глобальная переменная пуста или не отсутствует."""

    pass


class HttpStatusOkResponseError(Exception):
    """Ошибка, если HTTP-ответ не 200."""

    pass


class MissingErrorInformationAndNonOkStatus(Exception):
    """Информации об ошибке нет, но статус всё равно не 200."""

    pass
