from __future__ import annotations
from typing_extensions import Self
import typing
from enum import Enum
from dataclasses import dataclass
from bookkeeper.core import CategoryDeletePolicy


class CategoryField(str, Enum):
    name: str = "name"
    parent: str = "parent"


@dataclass
class AbstractCategory(typing.Protocol):
    model: AbstractCategoryModel
    id: int
    name: str

    def get_children(self) -> list[Self]: ...

    def get_parent(self) -> typing.Optional[Self]: ...

    def rename(self, new_name: str) -> Self: ...


class AbstractCategoryModel(typing.Protocol):

    def get_category_by_id(self, id: int) -> AbstractCategory:
        return self.get_categories_by_ids([id])[0]

    def get_categories_by_ids(self, ids: list[int]) -> list[AbstractCategory]: ...

    def get_root_categories(self) -> list[AbstractCategory]: ...

    def get_whole_subtree(
        self, category: typing.Optional[AbstractCategory] = None
    ) -> list[AbstractCategory]: ...

    def get_all_categories(self) -> list[AbstractCategory]: ...

    def add_category(
        self, name: str, parent: typing.Optional[AbstractCategory] = None
    ) -> AbstractCategory: ...

    def delete_category(
        self,
        cat: AbstractCategory,
        children_policy: CategoryDeletePolicy = CategoryDeletePolicy.delete,
    ) -> tuple[int, int]:
        """
        Delete category using policies.
        Returns (num_of_categories_touched, num_of_expenses_touched)
        """
        ...

    def rename_category(
        self, cat: AbstractCategory, new_name: str
    ) -> AbstractCategory: ...

    def update_category(
        self, cat: AbstractCategory, upd_data: dict[CategoryField, typing.Any]
    ) -> AbstractCategory: ...
