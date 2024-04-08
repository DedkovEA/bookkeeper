from __future__ import annotations
from typing import Callable, Optional
from PySide6 import QtWidgets, QtCore, QtGui

from bookkeeper.core import CategoryDeletePolicy, ExpensesHandlingPolicy
from bookkeeper.view.view_data import ViewCategory
from bookkeeper.view.pyside_gui_view.utility_widgets import LineEditsWithCaptions
from bookkeeper.exceptions import GUIInsertionError, GUIRemoveError


class CategoryTreeItem(QtWidgets.QTreeWidgetItem):

    def __init__(self, category: ViewCategory, *args, editable: bool = True, **kwargs):
        super().__init__([category.name], *args, **kwargs)
        if editable:
            self.setFlags(self.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
        else:
            self.setFlags(self.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        self.id = category.id


class CategorySelectionWidget(QtWidgets.QTreeWidget):
    def __init__(self, *args, editable: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        if editable:
            self.editable_categories = True
        else:
            self.editable_categories = False

        self.setColumnCount(1)
        self.shown_categories: dict[int, CategoryTreeItem] = {}
        # self._root = CategoryTreeItem(ViewCategory(-1000, "Categories"))
        # self._root.setFlags(self._root.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        # self.addTopLevelItem(self._root)

        self._root = QtWidgets.QTreeWidgetItem(["Categories"])
        self.setHeaderItem(self._root)

        # signals binding
        self.itemDoubleClicked.connect(self._edit_category_slot)
        self.itemChanged.connect(self._update_category_slot)

        if editable:
            self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            self.customContextMenuRequested.connect(self._show_popup_slot)

    def refresh_categories_list(self, categories: list[ViewCategory]) -> None:
        self.shown_categories = {}
        self.clear()
        # self._root = CategoryTreeItem(-1000, ["ROOT"])
        # self._root = CategoryTreeItem(ViewCategory(-1000, "ROOT"))
        # self._root.setFlags(self._root.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
        # self._root.setText(0, "ROOT")
        # self.addTopLevelItem(self._root)
        self.add_categories(categories)

    def add_category(self, category: ViewCategory) -> bool:
        if category.id in self.shown_categories:
            raise GUIInsertionError("Category inserting already exists")
        # if category.id == self._root.id:
        #     raise GUIInsertionError("Category id occasionally the same as in root")
        if category.parent is None:
            # new_cat = QtWidgets.QTreeWidgetItem()
            new_cat = CategoryTreeItem(category, editable=self.editable_categories)
            # new_cat.setText(0, category.name)
            self.addTopLevelItem(new_cat)
            self.shown_categories[category.id] = new_cat
        elif category.parent in self.shown_categories:
            # new_cat = QtWidgets.QTreeWidgetItem()
            new_cat = CategoryTreeItem(category, editable=self.editable_categories)
            # new_cat.setText(0, category.name)
            self.shown_categories[category.parent].addChild(new_cat)
            self.shown_categories[category.id] = new_cat
        else:
            return False
        return True

    def update_category(self, category: ViewCategory) -> bool:
        if category.id not in self.shown_categories:
            return False
        if category.parent not in self.shown_categories and category.parent is not None:
            return False
        cur_cat = self.shown_categories[category.id]
        cur_cat.setText(0, category.name)

        cur_parent = cur_cat.parent()
        if category.parent is not None:
            parent = self.shown_categories[category.parent]
            if cur_parent != parent:
                if cur_parent is None:
                    move_cat = self.takeTopLevelItem(self.indexOfTopLevelItem(cur_cat))
                else:
                    move_cat = cur_parent.takeChild(cur_parent.indexOfChild(cur_cat))
                parent.addChild(move_cat)
                assert move_cat == cur_cat
        else:
            if cur_parent is not None:
                move_cat = cur_parent.takeChild(cur_parent.indexOfChild(cur_cat))
                self.addTopLevelItem(move_cat)
                assert move_cat == cur_cat

        return True

    def add_categories(self, categories: list[ViewCategory]) -> None:
        not_inserted = categories.copy()

        # Protection against infinite loop
        k = 0
        while len(not_inserted) > k:
            category = not_inserted.pop(0)
            if not self.add_category(category):
                not_inserted.append(category)
                k += 1
                continue
            k = 0
        if k > 0:
            raise GUIInsertionError(
                (
                    "Some categories can not be inserted, since "
                    "no parents are provided for them."
                )
            )

    def update_categories_list(self, categories: list[ViewCategory]) -> None:
        cats_to_add = []
        for category in categories:
            if category.id in self.shown_categories:
                self.update_category(category)
            else:
                cats_to_add.append(category)
        self.add_categories(cats_to_add)

    def remove_categories(self, categories: list[int]) -> None:
        fail = False
        for category in categories:
            fail |= not self._remove_category(category)
        if fail:
            raise GUIRemoveError("Some of categories already are not in tree.")

    def _remove_category(self, category: int) -> bool:
        if category in self.shown_categories:
            cat_to_del = self.shown_categories[category]
            parent = cat_to_del.parent()
            children = cat_to_del.takeChildren()
            if parent is not None:
                parent.removeChild(cat_to_del)
                parent.addChildren(children)
            else:
                self.takeTopLevelItem(self.indexOfTopLevelItem(cat_to_del))
                self.addTopLevelItems(children)
            del self.shown_categories[category]
            return True
        else:
            return False

    # Widget methods
    def current_category_id(self) -> Optional[int]:
        if self.currentItem() is not None:
            return self.currentItem().id
        else:
            return None

    # Some methods for interaction

    # def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
    #     if event.button() == QtCore.Qt.MouseButton.RightButton:
    #         self._show_popup(event.globalPos())
    #         self.item_
    #     super().mousePressEvent(event)

    @QtCore.Slot()
    def _show_popup_slot(self, pos: QtCore.QPoint) -> None:
        self.context_menu_executed_item = self.itemAt(pos)
        context_menu = QtWidgets.QMenu(self)
        new_cat_act = QtGui.QAction("New category", self)
        new_cat_act.triggered.connect(self._invoke_creation_slot)
        context_menu.addAction(new_cat_act)
        del_cat_act = QtGui.QAction("Delete category", self)
        del_cat_act.triggered.connect(self._invoke_deletion_slot)
        context_menu.addAction(del_cat_act)
        context_menu.exec(self.mapToGlobal(pos))

    # Category creation slots
    @QtCore.Slot()
    def _invoke_creation_slot(self) -> None:
        dialog = CategoryCreationDialog()
        dialog.parameters_entered.connect(self._create_category_slot)
        dialog.exec()

    @QtCore.Slot()
    def _create_category_slot(self, name: str) -> None:
        parent = None
        if self.context_menu_executed_item is not None:
            parent = self.context_menu_executed_item.id
        # if parent != self._root.id:
        #     self._category_add_handler(name, parent)
        # else:
        #     self._category_add_handler(name)
        self._category_add_handler(name, parent)

    # Category deletion slots
    @QtCore.Slot()
    def _invoke_deletion_slot(self) -> None:
        if self.context_menu_executed_item is None:
            return
        if len(self._get_category_children_handler(
            self.context_menu_executed_item.id
        )) == 0:
            self._delete_category_slot(
                CategoryDeletePolicy.delete,
                ExpensesHandlingPolicy.delete,
            )
            return
        dialog = CategoryDeletionDialog()
        dialog.parameters_entered.connect(self._delete_category_slot)
        dialog.exec()

    @QtCore.Slot()
    def _delete_category_slot(
        self,
        children_policy: CategoryDeletePolicy,
        expenses_policy: ExpensesHandlingPolicy,
    ) -> None:
        self._category_delete_handler(
            self.context_menu_executed_item.id, children_policy, expenses_policy
        )
        # if self.currentItem() == self._root:
        #     pass
        # else:
        #     self._category_delete_handler(
        #         self.currentItem().id, children_policy, expenses_policy
        #     )

    # Category update slots
    @QtCore.Slot()
    def _edit_category_slot(self, item: CategoryTreeItem, column: int):
        self.editItem(item, column)

    @QtCore.Slot()
    def _update_category_slot(self, item: CategoryTreeItem, column: int):
        parent = item.parent()
        if parent is not None:
            parent = parent.id
        self._category_update_handler(ViewCategory(item.id, item.text(0), parent))

    #  Register some handlers for functionality
    def register_category_add_handler(
        self, handler: Callable[[str, Optional[int]], None]
    ) -> None:
        self._category_add_handler = handler

    def register_category_delete_handler(
        self,
        handler: Callable[[int, CategoryDeletePolicy, ExpensesHandlingPolicy], None],
    ) -> None:
        self._category_delete_handler = handler

    def register_category_update_handler(
        self, handler: Callable[[ViewCategory], None]
    ) -> None:
        self._category_update_handler = handler

    def register_get_category_children_handler(
        self, handler: Callable[[int], list[ViewCategory]]
    ) -> None:
        self._get_category_children_handler = handler


###################################################################################
#          Dialogs associated with operations on categories definition            #
###################################################################################


class CategoryCreationDialog(QtWidgets.QDialog):
    parameters_entered = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("New category creation")

        QBtn = (
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout()

        (name_le, name_layout) = LineEditsWithCaptions(["Name"])
        self.name_lineedit = name_le[0]
        self.layout.addLayout(name_layout)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        self.name_lineedit.setFocus()

    def accept(self):
        self.parameters_entered.emit(self.name_lineedit.text())
        super().accept()


class CategoryDeletionDialog(QtWidgets.QDialog):
    parameters_entered = QtCore.Signal(CategoryDeletePolicy, ExpensesHandlingPolicy)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Category deletion")

        QBtn = (
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout()

        children_policy_layout = QtWidgets.QVBoxLayout()
        children_policy_layout.addWidget(
            QtWidgets.QLabel("What to do with children categories?")
        )
        self.delete_children_RB = QtWidgets.QRadioButton("Delete recursively")
        self.move_children_RB = QtWidgets.QRadioButton("Move to parent category")
        self.children_group = QtWidgets.QButtonGroup()
        self.children_group.addButton(self.delete_children_RB)
        self.children_group.addButton(self.move_children_RB)
        children_policy_layout.addWidget(self.delete_children_RB)
        children_policy_layout.addWidget(self.move_children_RB)

        expenses_policy_layout = QtWidgets.QVBoxLayout()
        expenses_policy_layout.addWidget(
            QtWidgets.QLabel("What to do with expenses in deleted categories?")
        )
        self.delete_expenses_RB = QtWidgets.QRadioButton("Delete")
        self.move_expenses_RB = QtWidgets.QRadioButton("Move to parent category")
        self.expenses_group = QtWidgets.QButtonGroup()
        self.expenses_group.addButton(self.delete_expenses_RB)
        self.expenses_group.addButton(self.move_expenses_RB)
        expenses_policy_layout.addWidget(self.delete_expenses_RB)
        expenses_policy_layout.addWidget(self.move_expenses_RB)

        self.layout.addLayout(children_policy_layout)
        self.layout.addLayout(expenses_policy_layout)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        self.delete_children_RB.setChecked(True)
        self.delete_expenses_RB.setChecked(True)

    def accept(self):
        children_policy = CategoryDeletePolicy.delete
        expenses_handling = ExpensesHandlingPolicy.delete
        if self.move_children_RB.isChecked():
            children_policy = CategoryDeletePolicy.move
        if self.move_expenses_RB.isChecked():
            expenses_handling = ExpensesHandlingPolicy.move
        self.parameters_entered.emit(children_policy, expenses_handling)
        super().accept()


class CategorySelectionDialog(QtWidgets.QDialog):
    category_selected = QtCore.Signal(int)

    def __init__(self, categories: list[ViewCategory], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Select category")

        QBtn = (
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout()
        self.category_selection_wdg = CategorySelectionWidget(editable=False)
        self.category_selection_wdg.refresh_categories_list(categories)
        self.layout.addWidget(self.category_selection_wdg)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        # Some error messages
        self.none_category_error_msg = QtWidgets.QErrorMessage(self)
        self.none_category_error_msg.setWindowTitle("Error")

    def accept(self) -> None:
        cat_id = self.category_selection_wdg.current_category_id()
        if cat_id is None:
            self.none_category_error_msg.showMessage("You should select category")
            return
        self.category_selected.emit(cat_id)
        super().accept()
