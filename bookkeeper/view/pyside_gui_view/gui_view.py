from __future__ import annotations
import sys
from datetime import datetime
from typing import Callable, Any
from PySide6 import QtWidgets

from bookkeeper.core import CategoryDeletePolicy, ExpensesHandlingPolicy
from bookkeeper.view.abstract_view import AbstractView
from bookkeeper.view.view_data import ExpenseField, ViewExpense, ViewCategory
from bookkeeper.view.pyside_gui_view.expenses_table_widgets import ExpensesTableWidget
from bookkeeper.view.pyside_gui_view.expense_add_widgets import ExpenseAddWidget
from bookkeeper.view.pyside_gui_view.budget_widgets import BudgetWidget


class GUI_Based_View(AbstractView):
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.main_window = QtWidgets.QMainWindow()
        self.main_window.setWindowTitle("Bookkeeper")
        self.main_window.resize(400, 600)
        self.central_widget = BookKeeperLayout()
        self.main_window.setCentralWidget(self.central_widget)

    def start(self) -> None:
        self.main_window.show()
        sys.exit(self.app.exec())

    def refresh_expenses_table(self, expenses: list[ViewExpense]) -> None:
        self.central_widget.expenses_table_widget.full_update(expenses)

    def update_expenses(self, expenses: list[ViewExpense]) -> None:
        self.central_widget.expenses_table_widget.update(expenses)

    def remove_expenses(self, expenses: list[int]) -> None:
        self.central_widget.expenses_table_widget.remove_expenses(expenses)

    def expenses_shown(self) -> list[ViewExpense]:
        return self.central_widget.expenses_table_widget.expenses_shown()

    def refresh_categories(self, root_categories: list[ViewCategory]) -> None:
        self.central_widget.expense_add_widget.category_selection.refresh_categories_list(
            root_categories
        )

    def update_categories(self, categories: list[ViewCategory]) -> None:
        self.central_widget.expense_add_widget.category_selection.update_categories_list(
            categories
        )

    def remove_categories(self, categories: list[int]) -> None:
        self.central_widget.expense_add_widget.category_selection.remove_categories(
            categories
        )

    # Binding handlers from protocol

    def register_add_category_handler(
        self, handler: Callable[[str, int | None], None]
    ) -> None:
        self.central_widget.expense_add_widget.category_selection.\
            register_category_add_handler(
                handler
            )

    def register_delete_category_handler(
        self,
        handler: Callable[[int, CategoryDeletePolicy, ExpensesHandlingPolicy], None],
    ) -> None:
        self.central_widget.expense_add_widget.category_selection.\
            register_category_delete_handler(
                handler
            )

    def register_change_category_handler(
        self, handler: Callable[[ViewCategory], None]
    ) -> None:
        self.central_widget.expense_add_widget.category_selection.\
            register_category_update_handler(
                handler
            )

    def register_get_categories_handler(
        self, handler: Callable[[], list[ViewCategory]]
    ) -> None:
        self.central_widget.expenses_table_widget.register_get_categories_handler(
            handler
        )

    def register_add_expense_handler(
        self, handler: Callable[[int, int, datetime | None, str], None]
    ) -> None:
        self.central_widget.expense_add_widget.register_expense_add_handler(handler)

    def register_change_expense_handler(
        self, handler: Callable[[int, dict[ExpenseField, Any]], None]
    ) -> None:
        self.central_widget.expenses_table_widget.register_expense_update_handler(
            handler
        )

    def register_delete_expense_handler(self, handler: Callable[[int], None]) -> None:
        self.central_widget.expenses_table_widget.register_delete_expense_handler(
            handler
        )


class BookKeeperLayout(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expenses_table_widget = ExpensesTableWidget()
        self.budget_widget = BudgetWidget()
        self.expense_add_widget = ExpenseAddWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.expenses_table_widget, 4)
        layout.addWidget(self.budget_widget, 2)
        layout.addWidget(self.expense_add_widget, 3)
        self.setLayout(layout)
