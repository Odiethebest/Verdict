class VerdictError(Exception):
    """Base exception for all Verdict domain errors."""


class NotFoundError(VerdictError):
    def __init__(self, resource: str, id: int) -> None:
        self.resource = resource
        self.id = id
        super().__init__(f"{resource} with id={id} not found")


class ConflictError(VerdictError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ScoringError(VerdictError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ExperimentStateError(VerdictError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
