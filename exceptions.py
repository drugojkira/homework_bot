from telebot.apihelper import ApiException


class TelegramError(ApiException):
    """Ошибка: Сбой при отправке сообщения."""

    def __init__(self, message):
        """Конструктор класса."""
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        """Форматируем вывод сообщения об ошибке."""
        return f'{type(self).__name__} --> {self.message}'


class CustomSystemExit(Exception):
    """Переопределяем __str__ метод SystemExit."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{type(self).__name__} --> {self.message}'


class KeyError(KeyError):
    """Переопределяем __str__ метод KeyError."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{type(self).__name__} --> {self.message}'

# Определяем кастомные ошибки


class SendMessageError(Exception):
    """Ошибка: Сбой при отправке сообщения."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{type(self).__name__} --> {self.message}'


class EndpointAccessError(Exception):
    """Ошибка: Проблема с доступом к эндпоинт."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{type(self).__name__} --> {self.message}'


class HomeworksTypeError(Exception):
    """Ошибка: Не правильный тип ответа API."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{type(self).__name__} --> {self.message}'


class HomeworksEmptyError(Exception):
    """Ошибка: Словарь homework пуст."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'


class UnknownStatusError(Exception):
    """Ошибка: Неизвестный статус в homework_status."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{type(self).__name__} --> {self.message}'
