class APIResponseError(Exception):
    """Исключение при ошибках ответа API (код статуса != 200)."""


class JSONDecodeError(Exception):
    """Исключение при ошибке декодирования JSON ответа API."""
