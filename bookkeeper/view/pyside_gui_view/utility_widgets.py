from __future__ import annotations
from PySide6 import QtWidgets, QtCore


def LineEditsWithCaptions(params: list[str]) -> tuple[list[QtWidgets.QLineEdit],
                                                      QtWidgets.QGridLayout]:
    line_edits = []
    layout = QtWidgets.QGridLayout()
    for i in range(len(params)):
        layout.addWidget(QtWidgets.QLabel(params[i]), i, 0,
                         alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        le = QtWidgets.QLineEdit("")
        le.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(le, i, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
        line_edits.append(le)

    return (line_edits, layout)


class ConfirmationMessageBox(QtWidgets.QMessageBox):
    def __init__(self, msg: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_me = True
        self.setWindowTitle("Confirm action")
        self.setText(msg)
        self.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes |
                                QtWidgets.QMessageBox.StandardButton.No)
        self.setIcon(QtWidgets.QMessageBox.Icon.Question)
        self.cb = QtWidgets.QCheckBox("Don't ask again")
        self.setCheckBox(self.cb)
        self.cb.stateChanged.connect(self._state_change_signal)

    def exec(self) -> int:
        if self.show_me:
            return super().exec()
        else:
            return QtWidgets.QMessageBox.StandardButton.Yes

    def _state_change_signal(self, state: int) -> None:
        self.show_me = (state == QtCore.Qt.CheckState.Unchecked)
