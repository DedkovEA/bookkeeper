from __future__ import annotations
from typing import Protocol, Any, Optional
from dataclasses import dataclass, field
from bookkeeper.models.abstract_category_model import AbstractCategory
from datetime import datetime
from enum import Enum, IntFlag


@dataclass(init=False)
class AbstractExpense(Protocol):
    """
    Расходная операция.
    model - wrapper around database we need to ask for all info
    id - уникальный идентификатор
    amount - сумма
    category - категория расходов
    expense_date - дата расхода
    added_date - дата добавления в бд
    comment - комментарий
    """

    model: AbstractExpensesModel
    id: int
    amount: float
    # category: AbstractCategory
    expense_date: datetime = field(default_factory=datetime.now)
    added_date: datetime = field(default_factory=datetime.now)
    comment: str = ""

    def set_attribute(self, attr_name: str, value: Any) -> None:
        self.model.set_attributes(self, {attr_name: value})

    def get_category(self) -> AbstractCategory:
        return self.model.get_expense_category(self)

    def delete(self) -> None:
        self.model.delete_expense(self)


class ConstraintType(IntFlag):
    less: int = 1
    equal: int = 2
    greater: int = 4
    geq: int = 6
    leq: int = 3
    neq: int = 5


class ExpenseField(str, Enum):
    amount: str = "amount"
    category: str = "category"
    expense_date: str = "expense_date"
    added_date: str = "added_date"
    comment: str = "comment"


@dataclass
class ExpenseConstraint:
    """
    A constraint for select_expenses_by_constraints model function
    expense_field: the name of attribute on which constraint is set
    constraint_type: like / eq / geq / greater / leq / lower
    expression: with which to compare
    """

    expense_field: ExpenseField
    constraint_type: ConstraintType
    expression: Any


class AbstractExpensesModel(Protocol):
    def add_expense(
        self, amount: int, category: AbstractCategory, expense_date: datetime
    ) -> AbstractExpense: ...

    def delete_expense(self, expense: AbstractExpense) -> None: ...

    def delete_expenses(self, expenses: list[AbstractExpense]) -> None: ...

    def set_attributes(
        self, expense: AbstractExpense, attr_dict: dict[ExpenseField, Any]
    ) -> None: ...

    def get_expenses_by_ids(self, ids: list[int]) -> list[AbstractExpense]: ...

    def get_expense_by_id(self, id: int) -> AbstractExpense:
        return self.get_expenses_by_ids([id])[0]

    def get_expenses_by_constraints(
        self, constraints: list[ExpenseConstraint], max_num: Optional[int] = None
    ) -> list[AbstractExpense]: ...

    def get_expense_category(self, expense: AbstractExpense) -> AbstractCategory: ...

    def get_expense_amount_by_time_period(self, start: datetime, end: datetime) -> float:
        """
        Returns amount of all expences within specified time range
        """
        ...
