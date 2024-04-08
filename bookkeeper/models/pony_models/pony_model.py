from datetime import datetime
from pony.orm import Database, Required, PrimaryKey, Optional, Set
from bookkeeper.models.abstract_model import AbstractModel
from bookkeeper.models.pony_models.pony_category_model import PonyCategoryModel
from bookkeeper.models.pony_models.pony_expenses_model import PonyExpensesModel
from bookkeeper.models.pony_models.pony_budget_model import PonyBudgetModel


def define_database(**dbparams) -> Database:
    db = Database(**dbparams)

    class Category(db.Entity):
        # __metaclass__ = classmaker()
        id = PrimaryKey(int, auto=True)
        name = Required(str)
        expenses = Set("Expense")
        parent = Optional("Category", reverse="children")
        children = Set("Category", reverse="parent")

    class Budget(db.Entity):
        id = PrimaryKey(int, auto=True, unsigned=True)
        preset = Required(str, unique=True)
        daily = Optional(float)
        weekly = Optional(float)
        monthly = Optional(float)

    class Expense(db.Entity):
        id = PrimaryKey(int, auto=True, nullable=False)
        amount = Required(float)
        category = Required(Category)
        expense_date = Required(datetime, default=lambda: datetime.now())
        added_date = Required(datetime, default=lambda: datetime.now())
        comment = Optional(str)

    # db.bind(provider='sqlite', filename='database.sqlite', create_db=True)
    db.generate_mapping(create_tables=True)

    return db


class PonyModel(AbstractModel):
    def __init__(self, **dbparams):
        self.db = define_database(**dbparams)
        self.category_model = PonyCategoryModel(self, self.db)
        self.expenses_model = PonyExpensesModel(self, self.db)
        self.budget_model = PonyBudgetModel(self, self.db)
