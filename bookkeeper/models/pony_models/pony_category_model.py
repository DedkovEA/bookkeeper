from __future__ import annotations
from pony.orm import db_session, Database, Optional
from pony.orm.core import ObjectNotFound
import typing
from typing_extensions import Self
from dataclasses import dataclass

from bookkeeper.models.abstract_category_model import (
    AbstractCategory,
    AbstractCategoryModel,
    CategoryField,
)
from bookkeeper.core import (
    CategoryDeletePolicy,
    ExpensesHandlingPolicy,
)
from bookkeeper.models.abstract_model import AbstractModel
from bookkeeper.exceptions import NoDataError


@dataclass
class PonyCategory(AbstractCategory):
    model: PonyCategoryModel

    def get_parent(self) -> Optional[Self]:
        return self.model.get_parent(self)

    def get_children(self) -> list[Self]:
        return self.model.get_children(self)

    def rename(self, new_name: str) -> Self:
        return self.model.rename_category(self, new_name)

    def delete(
        self,
        children_policy: CategoryDeletePolicy = CategoryDeletePolicy.delete,
        expense_handling: ExpensesHandlingPolicy = ExpensesHandlingPolicy.delete,
    ) -> tuple[int, int]:
        return self.model.delete_category(
            self, children_policy=children_policy, expense_handling=expense_handling
        )

    def __hash__(self) -> int:
        """
        Just for helping purpose. Since each distinct category has unique id,
        we use it as hash
        """
        return self.id


class PonyCategoryModel(AbstractCategoryModel):
    def __init__(self, model: AbstractModel, database: Database):
        self.model = model
        self.db = database

    @db_session
    def add_category(
        self, name: str, parent: typing.Optional[AbstractCategory] = None
    ) -> PonyCategory:
        parent_category = None
        if parent is not None:
            parent_category = self.db.Category[parent.id]
        new_category = self.db.Category(name=name, parent=parent_category)
        new_category.flush()
        return self._form_ponycat(new_category)

    @db_session
    def delete_category(
        self,
        cat: PonyCategory,
        children_policy: CategoryDeletePolicy = CategoryDeletePolicy.delete,
        expense_handling: ExpensesHandlingPolicy = ExpensesHandlingPolicy.delete,
    ) -> tuple[int, int]:
        cat_to_del = self.db.Category[cat.id]
        (cat_touched, exp_touched) = self._del_cat(
            cat_to_del,
            children_policy=children_policy,
            expense_handling=expense_handling,
            parent_for_exps=cat_to_del.parent,
        )
        cat.id = None  # Corrupt PonyCategory object for safety
        cat.name = "DELETED"
        return (cat_touched, exp_touched)

    @db_session
    def _del_cat(
        self,
        cat_to_del: Self.db.Category,
        children_policy: CategoryDeletePolicy = CategoryDeletePolicy.delete,
        expense_handling: ExpensesHandlingPolicy = ExpensesHandlingPolicy.delete,
        parent_for_exps: typing.Optinal[Self.db.Category] = None,
    ) -> tuple[int, int]:
        cat_touched = 0
        exp_touched = 0
        if parent_for_exps is None:
            expense_handling = ExpensesHandlingPolicy.delete
        if children_policy == CategoryDeletePolicy.delete:
            for child in cat_to_del.children:
                (n1, n2) = self._del_cat(
                    child,
                    children_policy=children_policy,
                    expense_handling=expense_handling,
                    parent_for_exps=parent_for_exps,
                )
                cat_touched += n1
                exp_touched += n2
        if children_policy == CategoryDeletePolicy.move:
            parent = cat_to_del.parent
            for child in cat_to_del.children:
                child.parent = parent
                cat_touched += 1

        if expense_handling == ExpensesHandlingPolicy.delete:
            for exp in self.db.Expense.select(lambda e: e.category == cat_to_del):
                exp.delete()
                exp_touched += 1
        if expense_handling == ExpensesHandlingPolicy.move:
            for exp in self.db.Expense.select(lambda e: e.category == cat_to_del):
                exp.category = parent_for_exps
                exp_touched += 1
        cat_to_del.delete()
        return (cat_touched + 1, exp_touched)

    @db_session
    def get_parent(self, category: PonyCategory) -> typing.Optional[PonyCategory]:
        parent_category = self.db.Category[category.id].parent
        if parent_category is None:
            return None
        return self._form_ponycat(parent_category)

    @db_session
    def get_children(self, category: PonyCategory) -> list[PonyCategory]:
        children = []
        for child in self.db.Category[category.id].children:
            children.append(PonyCategory(model=self, id=child.id, name=child.name))
        return children

    @db_session
    def rename_category(self, cat: PonyCategory, new_name: str) -> PonyCategory:
        cat_to_rename = self.db.Category[cat.id]
        cat_to_rename.name = new_name
        cat_to_rename.flush()
        cat.name = new_name
        return cat

    @db_session
    def update_category(
        self, cat: PonyCategory, upd_data: dict[CategoryField, typing.Any]
    ) -> PonyCategory:
        cat_to_upd = self.db.Category[cat.id]
        if CategoryField.parent in upd_data:
            if upd_data[CategoryField.parent] is not None:
                upd_data[CategoryField.parent] = self.db.Category[
                    upd_data[CategoryField.parent]
                ]
        cat_to_upd.set(**upd_data)
        cat_to_upd.flush()
        return self._form_ponycat(cat_to_upd)

    @db_session
    def get_categories_by_ids(self, ids: list[int]) -> list[PonyCategory]:
        result = []
        fail = False
        for id in ids:
            try:
                loaded_cat = self.db.Category[id]
                result.append(self._form_ponycat(loaded_cat))
            except ObjectNotFound:
                fail = True
        if fail:
            raise NoDataError(
                ("There is no categories in database for one " "or more ids provided"),
                result,
            )
        return result

    @db_session
    def get_root_categories(self) -> list[PonyCategory]:
        root_cats = self.db.Category.select(lambda c: c.parent is None)
        result = [self._form_ponycat(rcat) for rcat in root_cats]
        return result

    @db_session
    def get_whole_subtree(
        self, category: typing.Optional[PonyCategory] = None
    ) -> list[PonyCategory]:

        result: list[PonyCategory] = []
        if category is None:
            root_cats = self.get_root_categories()
            for root_cat in root_cats:
                result.extend(self.get_whole_subtree(root_cat))
        else:
            result.append(category)
            for child in category.get_children():
                result.extend(self.get_whole_subtree(child))
        return result

    @db_session
    def get_all_categories(self) -> list[PonyCategory]:
        return self.get_whole_subtree()

    @db_session
    def _form_ponycat(self, cat: Self.db.Category) -> PonyCategory:
        return PonyCategory(model=self, id=cat.id, name=cat.name)
