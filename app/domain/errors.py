class DomainError(Exception):
    """Base type for domain-level errors (invariant violations)."""


class NotFound(DomainError):
    pass


class InvariantViolation(DomainError):
    pass


class ConcurrencyConflict(DomainError):
    pass
