from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from enum import IntEnum, Enum


@dataclass
class ViewCategory():
    id: int
    name: str
    parent: Optional[int] = None


@dataclass
class ViewExpense():
    id: int
    amount: str
    category: str
    expense_date: str
    comment: str


@dataclass
class ViewBudget():
    id: int
    caption: str
    daily: str
    weekly: str
    monthly: str
    exceeded: list[bool]
    editable: bool = True


class ExpenseField(str, Enum):
    amount: str = "amount"
    category: str = "category"
    expense_date: str = "expense_date"
    comment: str = "comment"


class FilterCondition(IntEnum):
    less: int = 1
    equal: int = 2
    greater: int = 4
    geq: int = 6
    leq: int = 3
    neq: int = 5


@dataclass
class ExpenseFilter():
    field: ExpenseField
    condition: FilterCondition
    expression: Any


_COMMON_DATETIME_FMT = "%d/%m/%Y"


def date_from_str(date: str) -> datetime:
    return datetime.strptime(date, _COMMON_DATETIME_FMT)
