from __future__ import annotations
from dataclasses import dataclass
from PySide6 import QtWidgets, QtCore, QtGui
from functools import partial
from typing import Callable, ClassVar, Any

from bookkeeper.view.view_data import ViewExpense, ExpenseField, ViewCategory
from bookkeeper.view.pyside_gui_view.category_select_widgets import (
    CategorySelectionDialog,
)
from bookkeeper.view.pyside_gui_view.utility_widgets import ConfirmationMessageBox
from bookkeeper.exceptions import GUIInsertionError, GUIRemoveError


class ExpenseTableItem(QtWidgets.QTableWidgetItem):
    def __init__(self, id, *args, **kwargs):
        self.id = id
        super().__init__(*args, **kwargs)


@dataclass
class ExpenseTableRowItem:
    id: int
    expense_date: ExpenseTableItem
    amount: ExpenseTableItem
    category: ExpenseTableItem
    comment: ExpenseTableItem

    column_mapping: ClassVar[dict[int, ExpenseField]] = {
        0: ExpenseField.expense_date,
        1: ExpenseField.amount,
        2: ExpenseField.category,
        3: ExpenseField.comment,
    }
    column_captions: ClassVar[dict[int, str]] = {
        0: "Date",
        1: "Amount",
        2: "Category",
        3: "Comment",
    }

    def __init__(self, expense: ViewExpense):
        self.id = expense.id
        self.expense_date = ExpenseTableItem(expense.id, expense.expense_date)
        self.amount = ExpenseTableItem(expense.id, expense.amount)
        self.category = ExpenseTableItem(expense.id, expense.category)
        self.comment = ExpenseTableItem(expense.id, expense.comment)
        self.expense_date.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.amount.setTextAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.category.setTextAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.comment.setTextAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.category.setFlags(
            self.category.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
        )

    def update(self, expense: ViewExpense) -> None:
        self.id = expense.id
        self.expense_date.setText(expense.expense_date)
        self.amount.setText(expense.amount)
        self.category.setText(expense.category)
        self.comment.setText(expense.comment)


class ExpensesTableWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        v_layout = QtWidgets.QVBoxLayout()
        v_layout.addWidget(QtWidgets.QLabel("Expenses"))

        self.shown_expenses: dict[int, ExpenseTableRowItem] = {}
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ExpenseTableRowItem.column_captions.values()
        )

        header = self.table.horizontalHeader()
        for i in range(3):
            header.setSectionResizeMode(
                i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
            )
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked
        )
        self.table.verticalHeader().hide()

        v_layout.addWidget(self.table)
        self.setLayout(v_layout)

        # Connecing signals
        self.table.itemChanged.connect(self._item_change_slot)
        self.table.itemDoubleClicked.connect(self._item_double_clicked_slot)
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_popup_slot)

        # Registering errors
        self.data_error_msg = QtWidgets.QErrorMessage()
        self.data_error_msg.setWindowTitle("Error")

        # Confirmation message
        self.delete_confirmation_msg = ConfirmationMessageBox(
            "This action can not be undone. Proceed?"
        )

    def set_row(self, i: int, expense: ViewExpense) -> None:
        if expense.id in self.shown_expenses:
            raise GUIInsertionError(
                "Attempt of expense insertion into Expense table with\
                                    already existed id"
            )
        set_row = ExpenseTableRowItem(expense)
        self.table.blockSignals(True)
        self.table.setItem(i, 0, set_row.expense_date)
        self.table.setItem(i, 1, set_row.amount)
        self.table.setItem(i, 2, set_row.category)
        self.table.setItem(i, 3, set_row.comment)
        self.table.blockSignals(False)
        self.shown_expenses[expense.id] = set_row

    def full_update(self, expenses: list[ViewExpense]) -> None:
        self.shown_expenses.clear()
        self.table.setRowCount(len(expenses))
        for i in range(len(expenses)):
            self.set_row(i, expenses[i])

    def update(self, expenses: list[ViewExpense]) -> None:
        to_add = []
        for expense in expenses:
            if expense.id in self.shown_expenses:
                self.table.blockSignals(True)
                self.shown_expenses[expense.id].update(expense)
                self.table.blockSignals(False)
            else:
                to_add.append(expense)
        self.add_expenses(to_add)

    def add_expenses(self, expenses: list[ViewExpense]) -> None:
        init_row_count = self.table.rowCount()
        self.table.setRowCount(init_row_count + len(expenses))
        failed = 0
        for i in range(len(expenses)):
            try:
                self.set_row(init_row_count + i - failed, expenses[i])
            except GUIInsertionError:
                failed += 1
        if failed > 0:
            self.table.setRowCount(init_row_count + len(expenses) - failed)
            raise GUIInsertionError(
                "While adding expenses some of them already were in table"
            )

    def remove_expenses(self, expenses: list[int]) -> None:
        failed = False
        for expense in expenses:
            if expense in self.shown_expenses:
                row = self.shown_expenses[expense].expense_date.row()
                del self.shown_expenses[expense]
                # del self.row_expense_map[row]
                self.table.removeRow(row)
            else:
                failed = True
        if failed:
            raise GUIRemoveError("Some of expenses already were not in table")

    def expenses_shown(self) -> list[ViewExpense]:
        return [self._form_view_expense(exp) for exp in self.shown_expenses.values()]

    # Slots
    @QtCore.Slot()
    def _item_change_slot(self, item: ExpenseTableItem) -> None:
        field = ExpenseTableRowItem.column_mapping[self.table.column(item)]
        id = item.id
        if field == ExpenseField.category:
            raise Exception("Some mess occured, category edited")
            # dlg = CategorySelectionDialog()
            # dlg.category_selected.connect(partial(self._update_category_slot, id))
            # dlg.exec()
            return
        try:
            self._expense_update_handler(id, {field: item.text()})
        except (TypeError, ValueError) as e:
            self.data_error_msg.showMessage(f"Incorrect data entered: {e}")
            self._expense_update_handler(id, {})

    @QtCore.Slot()
    def _item_double_clicked_slot(self, item: ExpenseTableItem) -> None:
        if (
            ExpenseTableRowItem.column_mapping[self.table.column(item)]
            == ExpenseField.category
        ):
            dlg = CategorySelectionDialog(self._get_categories_handler())
            dlg.category_selected.connect(partial(self._update_category_slot, item.id))
            dlg.exec()
        else:
            return

    @QtCore.Slot()
    def _update_category_slot(self, id: int, new_category_id: int) -> None:
        self._expense_update_handler(id, {ExpenseField.category: new_category_id})

    @QtCore.Slot()
    def _show_popup_slot(self, pos) -> None:
        self.context_menu_executed_item = self.table.itemAt(pos)
        context_menu = QtWidgets.QMenu(self)
        delete_expense_action = QtGui.QAction("Delete expense", self)
        delete_expense_action.triggered.connect(self._invoke_expense_deletion_slot)
        context_menu.addAction(delete_expense_action)
        context_menu.exec(self.table.mapToGlobal(pos))

    @QtCore.Slot()
    def _invoke_expense_deletion_slot(self) -> None:
        if (
            self.delete_confirmation_msg.exec()
            == QtWidgets.QMessageBox.StandardButton.Yes
        ):
            selected = self.table.selectedItems()
            for_deletion: list[int] = []
            # if len(selected) > 1:
            for item in selected:
                if item.id not in for_deletion:
                    for_deletion.append(item.id)
            self._delete_expenses_handler(for_deletion)
            # else:
            #     self._delete_expenses_handler([self.context_menu_executed_item.id])

    # Register handlers
    def register_expense_update_handler(
        self, handler: Callable[[int, dict[ExpenseField, Any]], None]
    ) -> None:
        self._expense_update_handler = handler

    def register_get_categories_handler(
        self, handler: Callable[[], list[ViewCategory]]
    ) -> None:
        self._get_categories_handler = handler

    def register_delete_expenses_handler(
            self, handler: Callable[[list[int]], None]
    ) -> None:
        self._delete_expenses_handler = handler

    # Utility functions
    def _form_view_expense(self, expense: ExpenseTableRowItem) -> ViewExpense:
        return ViewExpense(
            expense.id,
            expense.amount.text(),
            expense.category.text(),
            expense.expense_date.text(),
            expense.comment.text(),
        )
