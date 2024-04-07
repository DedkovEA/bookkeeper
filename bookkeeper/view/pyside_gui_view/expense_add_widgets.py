from PySide6 import QtWidgets, QtCore
from typing import Callable, Optional

from bookkeeper.view.pyside_gui_view.category_select_widgets import (
    CategorySelectionWidget,
)


class ExpenseAddWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        blayout = QtWidgets.QGridLayout()
        blayout.addWidget(
            QtWidgets.QLabel("Amount"),
            0,
            0,
            alignment=QtCore.Qt.AlignmentFlag.AlignLeft,
        )
        # blayout.addWidget(QtWidgets.QLabel("Category"), 1, 0,
        #                 alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.amount = QtWidgets.QLineEdit("")
        self.amount.setCursorPosition(0)
        self.amount.setFocus()
        self.amount.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self.category_selection = CategorySelectionWidget()

        self.add_button = QtWidgets.QPushButton("Add")
        blayout.addWidget(self.amount, 0, 1)
        blayout.addWidget(self.category_selection, 1, 0, 1, 2)
        blayout.addWidget(self.add_button, 2, 0, 1, 2)

        self.setLayout(blayout)

        self.add_button.clicked.connect(self._invoke_expense_addition)

        # Add some error messages:
        self.none_category_error_msg = QtWidgets.QErrorMessage()
        self.none_category_error_msg.setWindowTitle("Error")
        self.root_cat_error_msg = QtWidgets.QErrorMessage()
        self.root_cat_error_msg.setWindowTitle("Error")
        self.data_error_msg = QtWidgets.QErrorMessage()
        self.data_error_msg.setWindowTitle("Error")

    # slots for expense addition
    @QtCore.Slot()
    def _invoke_expense_addition(self) -> None:
        # if self.category_selection.currentItem() is None:
        if self.category_selection.current_category_id() is None:
            self.none_category_error_msg.showMessage(
                "It is required to select expense category!"
            )
            return
        if self.category_selection.currentItem() is self.category_selection._root:
            self.root_cat_error_msg.showMessage(
                'You can not add expense in technical "ROOT" category'
            )
            return
        try:
            self._expense_add_handler(
                self.amount.text(),
                #   self.category_selection.currentItem().id,
                self.category_selection.current_category_id(),
                None,
                "",
            )
        except (TypeError, ValueError) as e:
            self.data_error_msg.showMessage(f"Incorrect data entered: {e}")

    # register handlers for functionality

    def register_expense_add_handler(
        self, handler: Callable[[str, int, Optional[str], str], None]
    ) -> None:
        self._expense_add_handler = handler
