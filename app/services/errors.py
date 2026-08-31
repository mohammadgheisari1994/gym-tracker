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


class ResourceNotFound(ServiceError):
    """A requested row does not exist, or is not owned by the acting user."""


class DuplicateExercise(ServiceError):
    pass


class ExerciseInUse(ServiceError):
    """The exercise is referenced by a workout and cannot be deleted."""
