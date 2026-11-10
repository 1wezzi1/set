class DomainError(Exception):
    """Базовое исключение домена."""


class UserNotFound(DomainError):
    pass


class DebtNotFound(DomainError):
    pass


class InvalidOperation(DomainError):
    pass