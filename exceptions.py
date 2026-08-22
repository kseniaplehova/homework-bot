class APIResponseError(Exception):
    """Исключение при ошибках ответа API (код статуса != 200)."""

    pass


class JSONDecodeError(Exception):
    """Исключение при ошибке декодирования JSON ответа API."""

    pass
