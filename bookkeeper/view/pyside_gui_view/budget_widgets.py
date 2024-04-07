from PySide6 import QtWidgets


class BudgetWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Budget"))
        self.table = QtWidgets.QTableWidget(3, 2)
        self.table.setHorizontalHeaderLabels(["Spent", "Budget"])
        hheader = self.table.horizontalHeader()
        hheader.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        hheader.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setVerticalHeaderLabels(["Day", "Week", "Month"])
        # TODO: change for changes in budget limits
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        layout.addWidget(self.table)
        self.setLayout(layout)

    def set_item(self, i: int, j: int, text: str) -> None:
        self.table.setItem(i, j, QtWidgets.QTableWidgetItem(text))
