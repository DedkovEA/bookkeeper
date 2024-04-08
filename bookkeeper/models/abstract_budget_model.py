from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from typing import Protocol


@dataclass
class AbstractBudget(Protocol):
    id: int
    model: AbstractBudgetModel
    preset: str
    daily: float
    weekly: float
    monthly: float
    exceeded: list[bool]

    def update(self):
        self.model.update_budget(self)


# class BudgetField(str, Enum):
#     preset: str = "amount"
#     daily: str = "category"
#     weekly: str = "expense_date"
#     monthly: str = "added_date"


class AbstractBudgetModel(Protocol):
    def add_budget(
        preset: str, daily: float, weekly: float, monthly: float
    ) -> AbstractBudget:
        ...

    def get_budget_by_id(self, budget_id: int) -> AbstractBudget:
        return self.get_budgets_by_ids([budget_id])[0]

    def get_budgets_by_ids(self, budget_ids: list[int]) -> list[AbstractBudget]:
        ...

    def get_budget_preset(self, preset: str) -> Optional[AbstractBudget]:
        ...

    def update_budget(self, budget: AbstractBudget) -> None:
        ...

    def update_spent_budget(self) -> None:
        ...

    def get_spent_budget(self) -> None:
        ...
