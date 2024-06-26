from typing import Callable, Protocol, Optional, Any
from bookkeeper.core import CategoryDeletePolicy, ExpensesHandlingPolicy
from bookkeeper.view.view_data import (
    ViewCategory,
    ViewExpense,
    ExpenseField,
    ViewBudget,
)


class AbstractView(Protocol):
    def __init__(self):
        """
        Initialization of application in console/GUI
        """
        ...

    def start(self) -> None: ...

    def refresh_expenses_table(self, expenses: list[ViewExpense]) -> None:
        """
        Updates whole expenses table, populating it
        """
        ...

    def update_expenses(self, expenses_to_update: list[ViewExpense]) -> None:
        """
        Updates expenses with ids provided without refreshing whole table.
        If some expenses not exist, then adds them into table.
        Thus this method is necessary to call fof adding expenses.
        """
        ...

    def remove_expenses(self, expenses: list[int]) -> None:
        """
        Removes expenses with ids from expenses from table
        If there is no expenses with such ids, removes what it can and
        raises GUIRemoveError
        """
        ...

    def expenses_shown(self) -> list[ViewExpense]:
        """
        Returns a list of expenses, which is currently shown
        """
        ...

    def refresh_categories(self, categories: list[ViewCategory]) -> None:
        """
        Updates all categories (displays initial layout with whole tree rebuilt).
        All categories which you want to shown should be provided,
        all the others will be skipped while building initial category list.
        """
        ...

    def update_categories(self, categories_to_update: list[ViewCategory]) -> None:
        """
        Updates only categories with ids provided.
        If there is no such categories in current layout, adds them if necessary.
        Thus this method should be used for adding new categories to layout.
        """
        ...

    def remove_categories(self, categories: list[int]) -> None:
        """
        Removes categories provided from tree by their ids, moving their children to
        their parents.
        If there is no some of the categories,
        then removes whatever it can and raises GUIRemoveError
        """
        ...

    def refresh_budgets(self, budgets: list[ViewBudget]) -> None:
        """
        Erases all budgets shown. Show all provided budgets.
        """
        ...

    def update_budgets(self, budgets: list[ViewBudget]) -> None:
        """
        Updates shown budgets by their ids (in ViewBudget object).
        If there is no such budget, then add them and show.
        """
        ...

    def remove_budgets(self, budget_ids: list[int]) -> None:
        """
        Removes budgets by their ids.
        Raises GUIRemoveError if there is no such budgets shown.
        """
        ...

    # Methods for notifying Presenter

    def register_add_category_handler(
        self, handler: Callable[[str, Optional[int]], None]
    ) -> None:
        """
        Register handler for category addition in the form:
        handler ~ add_category(category_name, parent_category_id)
        """
        ...

    def register_delete_category_handler(
        self,
        handler: Callable[[int, CategoryDeletePolicy, ExpensesHandlingPolicy], None],
    ) -> None:
        """
        Register handler for category addition in the form:
        handler ~ delete_category(category_id, category_delete_policy,
        expenses_handling_policy)
        """
        ...

    def register_change_category_handler(
        self, handler: Callable[[ViewCategory], None]
    ) -> None:
        """
        Register handler for category addition in the form:
        handler ~ change_category(view_category (with id))
        """
        ...

    def register_get_category_children_handler(
        self, handler: Callable[[int], list[ViewCategory]]
    ) -> None:
        """
        Register handler for category addition in the form:
        handler ~ change_category(view_category (with id))
        """
        ...

    def register_add_expense_handler(
        self, handler: Callable[[str, int, Optional[str], str], None]
    ) -> None:
        """
        Register handler for expense addition in the form:
        handler ~ add_expense(amount, category_id, expense_date=None, comment="")
        """
        ...

    def register_delete_expenses_handler(
            self, handler: Callable[[list[int]], None]
    ) -> None:
        """
        Register handler for expense deletion in the form:
        handler ~ delete_expense(expense_id)
        """
        ...

    def register_change_expense_handler(
        self, handler: Callable[[int, dict[ExpenseField, Any]], None]
    ) -> None:
        """
        Register handler for expense changing in the form:
        handler ~ change_expense(expense_id, {field: value})
        """
        ...

    def register_get_categories_handler(
        self, handler: Callable[[], list[ViewCategory]]
    ) -> None:
        """
        Register handler returning list of all existing categories.
        """
        ...

    def register_add_budget_handler(
        self, handler: Callable[[str, str, str, str], None]
    ) -> None:
        """
        Register handler for budget addition in the form:
        handler ~ add_budget(caption, daily, weekly, monthly)
        """
        ...

    def register_delete_budget_handler(self, handler: Callable[[int], None]) -> None:
        """
        Register handler for budget deletion in the form:
        handler ~ delete_budget(budget_id)
        """
        ...

    def register_change_budget_handler(
        self, handler: Callable[[int, dict[str, str]], None]
    ) -> None:
        """
        Register handler for budget addition in the form:
        handler ~ change_expense(budget_id, dict{field: value})
        Field names are the same, as in ViewBudget fields
        Field editable and id is never in dict
        """
        ...
