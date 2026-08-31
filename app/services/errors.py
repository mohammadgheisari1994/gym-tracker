"""Domain errors raised by the service layer.

The web layer catches these and maps them to user-facing messages. They never
carry HTML or translated text.
"""


class ServiceError(Exception):
    """Base class for expected, user-recoverable service failures."""


class EmailAlreadyRegistered(ServiceError):
    pass


class InvalidCredentials(ServiceError):
    pass
