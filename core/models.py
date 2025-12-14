from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum, auto

@dataclass(frozen=True)
class LineDTO:
    account_id: str
    dare: float = 0.0
    avere: float = 0.0

@dataclass
class EntryDTO:
    date: str
    protocollo: Optional[str] = None
    documento: Optional[str] = None
    document_date: Optional[str] = None
    cliente_fornitore: Optional[str] = None
    descrizione: Optional[str] = None
    lines: List[LineDTO] = field(default_factory=list)
    client_reference_id: Optional[str] = None
    reversal_of: Optional[int] = None
    taxable_amount: Optional[float] = None
    vat_rate: Optional[float] = None
    vat_amount: Optional[float] = None
    is_sale: bool = False   # True=venda, False=acquisto

@dataclass
class EntryResult:
    success: bool
    entry_id: Optional[int] = None
    protocol: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error_details: List['LedgerError'] = field(default_factory=list)

# Error codes per validazione e posting
class ErrorCode(Enum):
    UNBALANCED = auto()
    INVALID_ACCOUNT = auto()
    PERIOD_CLOSED = auto()
    NEGATIVE_AMOUNT = auto()
    AMBIGUOUS_LINE = auto()
    EMPTY_LINES = auto()
    ALREADY_REVERSED = auto()
    DB_ERROR = auto()

@dataclass(frozen=True)
class LedgerError:
    code: ErrorCode
    message: str