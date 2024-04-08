from typing import Protocol
from bookkeeper.models.abstract_category_model import AbstractCategoryModel
from bookkeeper.models.abstract_expense_model import AbstractExpensesModel
from bookkeeper.models.abstract_budget_model import AbstractBudgetModel


class AbstractModel(Protocol):
    category_model: AbstractCategoryModel
    expenses_model: AbstractExpensesModel
    budget_model: AbstractBudgetModel

    def __init__(self, *args, **kwargs): ...
