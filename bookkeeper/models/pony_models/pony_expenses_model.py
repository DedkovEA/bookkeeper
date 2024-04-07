from __future__ import annotations
from pony.orm import db_session, Database, ObjectNotFound
import typing
from typing_extensions import Self
from dataclasses import dataclass
from datetime import datetime

from bookkeeper.models.abstract_expense_model import (
    AbstractExpense,
    AbstractCategory,
    AbstractExpensesModel,
    ExpenseConstraint,
    ConstraintType,
    ExpenseField,
)
from bookkeeper.models.abstract_model import AbstractModel
from bookkeeper.exceptions import (
    PrimaryKeyAssignmentError,
    ConstraintError,
    NoDataError,
)


@dataclass
class PonyExpense(AbstractExpense):
    model: PonyExpensesModel

    def __hash__(self) -> int:
        """
        Just for testing purpose. We use id as hash, since it is unique
        """
        return self.id


class PonyExpensesModel(AbstractExpensesModel):
    def __init__(self, model: AbstractModel, database: Database):
        self.model = model
        self.db = database

    @db_session
    def add_expense(
        self,
        amount: float,
        category: AbstractCategory,
        expense_date: typing.Optional[datetime] = None,
        comment: typing.Optional[str] = None,
    ) -> PonyExpense:
        raw_kwargs = {"expense_date": expense_date, "comment": comment}
        kwargs = {
            kwarg: raw_kwargs[kwarg]
            for kwarg in raw_kwargs
            if raw_kwargs[kwarg] is not None
        }
        new_expense = self.db.Expense(
            amount=amount, category=self.db.Category[category.id], **kwargs
        )
        new_expense.flush()
        # return PonyExpense(model=self,
        #                    id=new_expense.id,
        #                    amount=amount,
        #                 #    category=category,
        #                    expense_date=new_expense.expense_date,
        #                    added_date=new_expense.added_date,
        #                    comment=new_expense.comment)
        return self._form_ponyexpense(new_expense)

    @db_session
    def delete_expense(self, expense: PonyExpense) -> None:
        expense_to_delete = self.db.Expense[expense.id]
        expense_to_delete.delete()
        expense_to_delete.flush()
        # Corrupt deleted object
        expense.id = None
        # expense.category = None
        expense.comment = "DELETED"

    @db_session
    def get_expenses_by_ids(self, ids: list[int]) -> list[PonyExpense]:
        result = []
        fail = False
        for id in ids:
            try:
                loaded_exp = self.db.Expense[id]
                # atrs = loaded_exp.to_dict(exclude="category")
                # result.append(PonyExpense(model=self, **atrs))
                result.append(self._form_ponyexpense(loaded_exp))
            except ObjectNotFound:
                fail = True
        if fail:
            raise NoDataError(
                "There is no expenses in database for one \
                              or more ids provided",
                result,
            )
        return result

    @db_session
    def get_expenses_by_constraints(
        self, constraints: list[ExpenseConstraint], max_num: typing.Optional[int] = None
    ) -> list[PonyExpense]:
        for c in constraints:
            if not self._validate_constraint(c):
                raise (ConstraintError("Invalid constraint provided"))

        query = self.db.Expense.select()
        for c in constraints:
            if c.expense_field == ExpenseField.category:
                cat_to_cmp = self.db.Category[c.expression.id]
                query = query.where(lambda e: e.category == cat_to_cmp)
            elif c.expense_field == ExpenseField.comment:
                query = query.where(lambda e: e.comment == c.expression)
            else:

                def check(f, expr, lfl, eqfl, gfl):
                    return (
                        (f < expr and lfl) or (f == expr and eqfl) or (f > expr and gfl)
                    )

                flags = [
                    bool(c.constraint_type & ConstraintType.less),
                    bool(c.constraint_type & ConstraintType.equal),
                    bool(c.constraint_type & ConstraintType.greater),
                ]
                query = query.where(
                    lambda e: check(
                        getattr(e, c.expense_field),
                        c.expression,
                        flags[0],
                        flags[1],
                        flags[2],
                    )
                )

        # def constraint_filter(expense: self.db.Expense):
        #     for c in constraints:
        #         if not self._check_constraint(c, expense):
        #             return False
        # expenses_got = self.db.Expense.select(constraint_filter)
        if max_num is None or max_num < 0:
            expenses_got = query[:]
        else:
            expenses_got = query[:max_num]
        result = []
        for exps in expenses_got:
            # atrs = exps.to_dict(exclude="category")
            # result.append(PonyExpense(model=self, **atrs))
            result.append(self._form_ponyexpense(exps))
        return result

    def _validate_constraint(self, constraint: ExpenseConstraint) -> bool:
        if constraint.constraint_type != ConstraintType.equal and (
            constraint.expense_field == ExpenseField.category
            or constraint.expense_field == ExpenseField.comment
        ):
            return False
        return True

    @db_session
    def set_attributes(
        self, expense: PonyExpense, attr_dict: dict[ExpenseField, typing.Any]
    ) -> None:
        if "id" in attr_dict.keys():
            raise (
                PrimaryKeyAssignmentError(
                    'Attribute "id" of PonyExpense \
                                            object can not be reassigned.'
                )
            )
        new_attrs = attr_dict.copy()
        if ExpenseField.category in attr_dict.keys():
            # WARNING : Possibly corrupted dictionary
            attr_dict[ExpenseField.category] = self.db.Category[
                attr_dict[ExpenseField.category].id
            ]
            del new_attrs[ExpenseField.category]
        expense_to_modify = self.db.Expense[expense.id]
        expense_to_modify.set(**attr_dict)
        expense_to_modify.flush()
        for key in new_attrs:
            setattr(expense, key, new_attrs[key])

    @db_session
    def get_expense_category(self, expense: PonyExpense) -> AbstractCategory:
        return self.model.category_model.get_category_by_id(
            self.db.Expense[expense.id].category.id
        )

    # Utility functions
    @db_session
    def _form_ponyexpense(self, expense: Self.db.Expense) -> PonyExpense:
        atrs = expense.to_dict(exclude="category")
        return PonyExpense(model=self, **atrs)
