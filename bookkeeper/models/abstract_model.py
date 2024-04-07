from typing import Protocol
from bookkeeper.models.abstract_category_model import AbstractCategoryModel
from bookkeeper.models.abstract_expense_model import AbstractExpensesModel


class AbstractModel(Protocol):
    category_model: AbstractCategoryModel
    expenses_model: AbstractExpensesModel

    def __init__(self, *args, **kwargs): ...
