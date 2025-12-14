# core/errors.py
from dataclasses import dataclass
from enum import Enum, auto

class ErrorCode(Enum):
    UNBALANCED = auto()
    INVALID_ACCOUNT = auto()
    PERIOD_CLOSED = auto()
    NEGATIVE_AMOUNT = auto()
    AMBIGUOUS_LINE = auto()
    EMPTY_LINES = auto()

@dataclass(frozen=True)
class LedgerError:
    code: ErrorCode
    message: str
