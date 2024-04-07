from bookkeeper.models.abstract_model import AbstractModel
from bookkeeper.models.abstract_category_model import (
    AbstractCategory,
    CategoryField,
)
from bookkeeper.models.abstract_expense_model import AbstractExpense
from bookkeeper.models.abstract_expense_model import ExpenseField as ModelExpenseField
from bookkeeper.view.abstract_view import AbstractView
from bookkeeper.view.view_data import (
    ViewCategory,
    ViewExpense,
    date_from_str,
    _COMMON_DATETIME_FMT,
    ExpenseField,
)
from bookkeeper.core import CategoryDeletePolicy, ExpensesHandlingPolicy

from typing import Optional, Any
from datetime import datetime


class Presenter:
    # Some constants
    _MAX_EXPENSES_SHOWN: int = 100

    def __init__(self, view_instance: AbstractView, model_instance: AbstractModel):
        self.view = view_instance
        self.model = model_instance
        self.refresh_categories()
        self.refresh_expenses()

        # Register handlers
        self.view.register_add_category_handler(self.add_category)
        self.view.register_delete_category_handler(self.delete_category)
        self.view.register_change_category_handler(self.change_category)
        self.view.register_get_categories_handler(self.get_categories)
        self.view.register_get_children_handler(self.get_children)
        self.view.register_add_expense_handler(self.add_expense)
        self.view.register_change_expense_handler(self.change_expense)
        self.view.register_delete_expense_handler(self.delete_expense)

        self.view.start()

    def refresh_categories(self) -> None:
        all_cats = self.model.category_model.get_all_categories()
        all_cats_view = [self._form_view_category(cat) for cat in all_cats]
        self.view.refresh_categories(all_cats_view)

    def refresh_expenses(self) -> None:
        all_expenses = self.model.expenses_model.get_expenses_by_constraints(
            [], max_num=self._MAX_EXPENSES_SHOWN
        )
        view_expenses = [self._form_view_expense(exp) for exp in all_expenses]
        self.view.refresh_expenses_table(view_expenses)

    def _form_view_category(self, category: AbstractCategory) -> ViewCategory:
        parent = category.get_parent()
        if parent is None:
            return ViewCategory(category.id, category.name, None)
        else:
            return ViewCategory(category.id, category.name, parent.id)

    def _form_view_expense(self, expense: AbstractExpense) -> ViewExpense:
        return ViewExpense(
            expense.id,
            self._represent_amount(expense.amount),
            expense.get_category().name,
            self._represent_date(expense.expense_date),
            expense.comment,
        )

    def _represent_amount(self, amount: float) -> str:
        return "{:.2f}".format(amount)

    def _represent_date(self, date: datetime) -> str:
        return date.strftime(_COMMON_DATETIME_FMT)

    def add_category(self, name: str, parent: Optional[int] = None) -> None:
        if parent is not None:
            parent = self.model.category_model.get_category_by_id(parent)
        added_category = self.model.category_model.add_category(name, parent)
        self.view.update_categories([self._form_view_category(added_category)])

    def delete_category(
        self,
        id: int,
        children_policy: CategoryDeletePolicy,
        expenses_policy: ExpensesHandlingPolicy,
    ) -> None:
        # TODO : rewrite delete_category in such way it returns id's of removed categories
        # and expenses and use view.remove_categories functions.
        self.model.category_model.delete_category(
            self.model.category_model.get_category_by_id(id),
            children_policy,
            expenses_policy,
        )
        self.refresh_categories()
        self.refresh_expenses()

    def change_category(self, category: ViewCategory) -> None:
        cat_to_change = self.model.category_model.get_category_by_id(category.id)
        if self._form_view_category(cat_to_change) == category:
            return
        attr_dict = {
            CategoryField.name: category.name,
            CategoryField.parent: category.parent,
        }
        changed_cat = self.model.category_model.update_category(
            cat_to_change, attr_dict
        )
        self.view.update_categories([self._form_view_category(changed_cat)])
        exps_shown = self.view.expenses_shown()
        new_exps = [
            self._form_view_expense(exp)
            for exp in self.model.expenses_model.get_expenses_by_ids(
                [e.id for e in exps_shown]
            )
        ]
        self.view.update_expenses(new_exps)

    def get_categories(self) -> list[ViewCategory]:
        return [
            self._form_view_category(cat)
            for cat in self.model.category_model.get_all_categories()
        ]
    
    def get_children(self, category_id: int) -> ViewCategory:
        return [
            self._form_view_category(child) 
            for child in 
            self.model.category_model.get_category_by_id(category_id).get_children()
        ]

    def add_expense(
        self,
        amount: str,
        category: int,
        expense_date: Optional[str] = None,
        comment: str = "",
    ) -> None:
        famount = float(amount)
        date_exp_date = None
        if expense_date is not None:
            date_exp_date = date_from_str(expense_date)
        new_expense = self.model.expenses_model.add_expense(
            famount,
            self.model.category_model.get_category_by_id(category),
            date_exp_date,
            comment,
        )
        self.view.update_expenses([self._form_view_expense(new_expense)])

    def change_expense(self, id: int, changes: dict[ExpenseField, Any]) -> None:
        model_changes: dict[ModelExpenseField, Any] = {}
        for key in changes:
            if key == ExpenseField.category:
                model_changes[ModelExpenseField.category] = (
                    self.model.category_model.get_category_by_id(changes[key])
                )
                continue
            if key == ExpenseField.amount:
                model_changes[ModelExpenseField.amount] = float(changes[key])
                continue
            if key == ExpenseField.expense_date:
                model_changes[ModelExpenseField.expense_date] = date_from_str(
                    changes[key]
                )
                continue
            if key == ExpenseField.comment:
                model_changes[ModelExpenseField.comment] = changes[key]
                continue

        exp_to_change = self.model.expenses_model.get_expense_by_id(id)
        self.model.expenses_model.set_attributes(exp_to_change, model_changes)
        self.view.update_expenses([self._form_view_expense(exp_to_change)])

    def delete_expense(self, expense_id: int) -> None:
        expense_to_remove = self.model.expenses_model.get_expense_by_id(expense_id)
        self.model.expenses_model.delete_expense(expense_to_remove)
        self.view.remove_expenses([expense_id])
