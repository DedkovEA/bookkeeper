from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, Callable
from PySide6 import QtWidgets, QtCore, QtGui

from bookkeeper.view.view_data import ViewBudget
from bookkeeper.exceptions import (
    GUIInsertionError,
    GUIRemoveError,
    NoAccessError,
)


class BudgetTableItem(QtWidgets.QTableWidgetItem):
    def __init__(self, parent: BudgetTableColumn, *args, **kwargs):
        self.parent = parent
        super().__init__(*args, **kwargs)


@dataclass
class BudgetTableColumn:
    id: int
    column: int
    caption: BudgetTableItem
    daily: BudgetTableItem
    weekly: BudgetTableItem
    monthly: BudgetTableItem

    row_mapping: ClassVar[dict[int, str]] = {
        0: "daily",
        1: "weekly",
        2: "monthly",
    }
    row_caption_items: ClassVar[dict[int, QtWidgets.QTreeWidgetItem]] = {
        0: QtWidgets.QTableWidgetItem("Daily"),
        1: QtWidgets.QTableWidgetItem("Weekly"),
        2: QtWidgets.QTableWidgetItem("Monthly"),
    }

    def __init__(self, budget: ViewBudget, column: int = -1):
        self.column = column
        self.id = budget.id
        self.caption = BudgetTableItem(self, budget.caption)
        self.daily = BudgetTableItem(self, budget.daily)
        self.weekly = BudgetTableItem(self, budget.weekly)
        self.monthly = BudgetTableItem(self, budget.monthly)

        self.caption.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.daily.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.weekly.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.monthly.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self._update_background(budget)
        self._update_flags(budget)

    def _update_background(self, budget: ViewBudget) -> None:
        if budget.exceeded[0]:
            self.daily.setBackground(QtGui.QColor(255, 255, 255, 0))
        else:
            self.daily.setBackground(QtGui.QColor(255, 0, 0, 64))
        if budget.exceeded[1]:
            self.weekly.setBackground(QtGui.QColor(255, 255, 255, 0))
        else:
            self.weekly.setBackground(QtGui.QColor(255, 0, 0, 64))
        if budget.exceeded[2]:
            self.monthly.setBackground(QtGui.QColor(255, 255, 255, 0))
        else:
            self.monthly.setBackground(QtGui.QColor(255, 0, 0, 64))

    def _update_flags(self, budget: ViewBudget) -> None:
        if budget.editable:
            self.caption.setFlags(
                self.caption.flags() | QtCore.Qt.ItemFlag.ItemIsEditable
            )
            self.daily.setFlags(self.daily.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
            self.weekly.setFlags(
                self.weekly.flags() | QtCore.Qt.ItemFlag.ItemIsEditable
            )
            self.monthly.setFlags(
                self.monthly.flags() | QtCore.Qt.ItemFlag.ItemIsEditable
            )
        else:
            self.caption.setFlags(
                self.caption.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
            )
            self.daily.setFlags(self.daily.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            self.weekly.setFlags(
                self.weekly.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
            )
            self.monthly.setFlags(
                self.monthly.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
            )

    def update(self, budget: ViewBudget) -> None:
        self.caption.setText(budget.caption)
        self.daily.setText(budget.daily)
        self.weekly.setText(budget.weekly)
        self.monthly.setText(budget.monthly)
        self._update_background(budget)
        self._update_flags(budget)

    def any_item(self) -> BudgetTableItem:
        return self.daily


class BudgetWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Budget"))
        self.table = QtWidgets.QTableWidget(3, 0)
        for row_num in BudgetTableColumn.row_caption_items:
            self.table.setVerticalHeaderItem(
                row_num,
                QtWidgets.QTableWidgetItem(
                    BudgetTableColumn.row_caption_items[row_num]
                ),
            )
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked
        )
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.table.setMinimumHeight(120)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            QtWidgets.QSizePolicy.Policy.Maximum,
        )

        self.budgets_shown: dict[int, BudgetTableColumn] = {}

        # Connecing signals
        self.table.itemChanged.connect(self._item_change_slot)
        # self.table.itemDoubleClicked.connect(self._item_double_clicked_slot)
        self.table.horizontalHeader().sectionDoubleClicked.connect(
            self._header_doubleclick_slot
        )
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_popup_slot)

        # Register error messages
        self.data_error_msg = QtWidgets.QErrorMessage()
        self.data_error_msg.setWindowTitle("Error")
        self.access_error_msg = QtWidgets.QErrorMessage()
        self.access_error_msg.setWindowTitle("Error")

    def initialize_column(self, column_num: int, budget: ViewBudget) -> None:
        if budget.id in self.budgets_shown:
            raise (GUIInsertionError("Budget with id provided is already in table"))
        column_set = BudgetTableColumn(budget, column=column_num)
        self.table.blockSignals(True)
        for row in BudgetTableColumn.row_mapping:
            self.table.setItem(
                row, column_num, getattr(column_set, BudgetTableColumn.row_mapping[row])
            )
            self.table.setHorizontalHeaderItem(column_num, column_set.caption)
        self.table.blockSignals(False)
        self.budgets_shown[budget.id] = column_set

    def add_budgets(self, budgets: list[ViewBudget]) -> None:
        init_col_num = self.table.columnCount()
        self.table.setColumnCount(init_col_num + len(budgets))
        failed = 0
        hheader = self.table.horizontalHeader()
        for i in range(len(budgets)):
            try:
                self.initialize_column(init_col_num + i - failed, budgets[i])
                hheader.setSectionResizeMode(
                    init_col_num + i - failed, QtWidgets.QHeaderView.ResizeMode.Stretch
                )
            except GUIInsertionError:
                failed += 1
        if failed > 0:
            self.table.setRowCount(init_col_num + len(budgets) - failed)
            raise (
                GUIInsertionError(
                    "While adding budgets some of them already were in table"
                )
            )

    def update_budgets(self, budgets: list[ViewBudget]) -> None:
        to_add = []
        for budget in budgets:
            if budget.id in self.budgets_shown:
                self.table.blockSignals(True)
                self.budgets_shown[budget.id].update(budget)
                self.table.blockSignals(False)
            else:
                to_add.append(budget)
        self.add_budgets(to_add)

    def refresh_budgets(self, budgets: list[ViewBudget]) -> None:
        self.table.setColumnCount(0)
        # for row_num in BudgetTableColumn.row_caption_items:
        #     self.table.setVerticalHeaderItem(
        #         row_num, QtWidgets.QTableWidgetItem(
        #             BudgetTableColumn.row_caption_items[row_num]
        #         )
        #     )
        self.budgets_shown.clear()
        self.add_budgets(budgets)

    def remove_budgets(self, budget_ids: list[int]) -> None:
        failed = 0
        for budget_id in budget_ids:
            if budget_id not in self.budgets_shown:
                failed += 1
                continue
            self.table.removeColumn(
                self.table.column(self.budgets_shown[budget_id].any_item())
            )
            del self.budgets_shown[budget_id]
        if failed > 0:
            raise GUIRemoveError(
                f"{failed} budget ids were not found, thus not removed"
            )

    def _invoke_budget_preset_renaming(self, id: int):
        text, ok = QtWidgets.QInputDialog.getText(
            self, "Rename preset", "New name:", QtWidgets.QLineEdit.EchoMode.Normal, ""
        )
        if ok:
            try:
                self._budget_update_handler(id, {"caption": text})
            # except NoAccessToGenericValuesError as e:
            #     self.access_error_msg.showMessage(f"No access: {e}")
            except NoAccessError as e:
                self.access_error_msg.showMessage(f"No access: {e}")
                self._budget_update_handler(id, {})

    # Slots
    @QtCore.Slot()
    def _item_change_slot(self, item: BudgetTableItem) -> None:
        id = item.parent.id
        field = BudgetTableColumn.row_mapping[item.row()]
        try:
            self._budget_update_handler(id, {field: item.text()}),
        except (TypeError, ValueError) as e:
            self.data_error_msg.showMessage(f"Incorrect data entered: {e}")
            self._budget_update_handler(id, {})
        except NoAccessError as e:
            self.access_error_msg.showMessage(f"No access: {e}")
            self._budget_update_handler(id, {})

    # @QtCore.Slot()
    # def _item_double_clicked_slot(self, item: BudgetTableItem) -> None:
    #     if (
    #         BudgetTableColumn.row_mapping[self.table.column(item)]
    #         == ExpenseField.category
    #     ):
    #         dlg = CategorySelectionDialog(self._get_categories_handler())
    #         dlg.category_selected.connect(partial(self._update_category_slot, item.id))
    #         dlg.exec()
    #     else:
    #         return

    @QtCore.Slot()
    def _show_popup_slot(self, pos) -> None:
        self.context_menu_executed_item = self.table.itemAt(pos)
        context_menu = QtWidgets.QMenu(self)
        rename_budget_action = QtGui.QAction("Rename preset", self)
        rename_budget_action.triggered.connect(self._invoke_budget_preset_renaming_slot)
        context_menu.addAction(rename_budget_action)
        context_menu.exec(self.table.mapToGlobal(pos))

    @QtCore.Slot()
    def _header_doubleclick_slot(self, index: int) -> None:
        self._invoke_budget_preset_renaming(self.table.item(0, index).parent.id)

    # Registering handlers
    def register_budget_update_handler(
        self, handler: Callable[[int, dict[str, str]], None]
    ) -> None:
        self._budget_update_handler = handler
