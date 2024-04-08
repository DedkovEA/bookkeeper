from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Optional
from typing_extensions import Self
from pony.orm import Database, db_session, ObjectNotFound, select

from bookkeeper.models.abstract_model import AbstractModel
from bookkeeper.models.abstract_budget_model import AbstractBudgetModel, AbstractBudget
from bookkeeper.exceptions import NoDataError


@dataclass
class PonyBudget(AbstractBudget):
    model: PonyBudgetModel


class PonyBudgetModel(AbstractBudgetModel):
    _BUDGET_SPENT_GEN_PRESET: str = "BUDGET_SPENT_GEN_PRESET"

    @db_session
    def __init__(self, model: AbstractModel, db: Database):
        self.model = model
        self.db = db
        self._budget_spent_id = select(
            b.id for b in self.db.Budget if b.preset == self._BUDGET_SPENT_GEN_PRESET
        ).first()
        if self._budget_spent_id is None:
            budget_spent = self.db.Budget(preset=self._BUDGET_SPENT_GEN_PRESET)
            budget_spent.flush()
            self._budget_spent_id = budget_spent.id
            self.update_spent_budget()
            budget_spent.flush()

    @db_session
    def _form_pony_budget(self, budget: Self.db.Budget) -> PonyBudget:
        return PonyBudget(
            id=budget.id,
            model=self,
            preset=budget.preset,
            daily=budget.daily,
            weekly=budget.weekly,
            monthly=budget.monthly,
            exceeded=self.check_if_exceed(budget),
        )

    @db_session
    def add_budget(
        self, preset: str, daily: float, weekly: float, monthly: float
    ) -> PonyBudget:
        added_budget = self.db.Budget(
            preset=preset,
            daily=daily,
            weekly=weekly,
            monthly=monthly,
        )
        added_budget.flush()
        return self._form_pony_budget(added_budget)

    @db_session
    def get_budgets_by_ids(self, budget_ids: list[int]) -> list[PonyBudget]:
        result = []
        fail = False
        for id in budget_ids:
            try:
                loaded_budget = self.db.Budget[id]
                result.append(self._form_pony_budget(loaded_budget))
            except ObjectNotFound:
                fail = True
        if fail:
            raise NoDataError(
                ("There is no budgets in database for one or more ids provided"),
                result,
            )
        return result

    @db_session
    def get_budget_preset(self, preset: str) -> Optional[PonyBudget]:
        result = self.db.Budget.select(lambda b: b.preset == preset).first()
        if result is None:
            return None
        return self._form_pony_budget(result)

    @db_session
    def update_budget(self, budget: PonyBudget) -> None:
        try:
            budget_to_upd = self.db.Budget[budget.id]
        except ObjectNotFound:
            raise NoDataError("There is no budget with such id in database")
        budget_to_upd.preset = budget.preset
        budget_to_upd.daily = budget.daily
        budget_to_upd.weekly = budget.weekly
        budget_to_upd.monthly = budget.monthly
        budget_to_upd.flush()
        budget.exceeded = self._form_pony_budget(budget_to_upd).exceeded

    @db_session
    def update_spent_budget(self) -> None:
        end_of_day = datetime.combine(datetime.now(), time.max)
        start_of_day = datetime.combine(end_of_day, time.min)
        start_of_week = start_of_day - timedelta(days=end_of_day.weekday())
        start_of_month = start_of_day.replace(day=1)
        self.db.Budget[self._budget_spent_id].set(
            daily=self.model.expenses_model.get_expense_amount_by_time_period(
                start_of_day, end_of_day
            ),
            weekly=self.model.expenses_model.get_expense_amount_by_time_period(
                start_of_week, end_of_day
            ),
            monthly=self.model.expenses_model.get_expense_amount_by_time_period(
                start_of_month, end_of_day
            ),
        )

    @db_session
    def get_spent_budget(self) -> None:
        return self._form_pony_budget(self.db.Budget[self._budget_spent_id])

    @db_session
    def check_if_exceed(self, budget: Self.db.Budget) -> list[bool]:
        budget_spent = self.db.Budget[self._budget_spent_id]
        return [
            budget_spent.daily <= budget.daily,
            budget_spent.weekly <= budget.weekly,
            budget_spent.monthly <= budget.monthly,
        ]
