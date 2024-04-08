from datetime import datetime
import pytest

from bookkeeper.core import (
    CategoryDeletePolicy,
    ExpensesHandlingPolicy,
)
from bookkeeper.models.abstract_expense_model import (
    ConstraintType,
    ExpenseConstraint,
    ExpenseField,
)
from bookkeeper.models.pony_models.pony_model import PonyModel
from bookkeeper.models.pony_models.pony_category_model import (
    PonyCategoryModel,
)
from bookkeeper.models.pony_models.pony_expenses_model import (
    PonyExpensesModel,
)
from bookkeeper.exceptions import (
    NoDataError,
    PrimaryKeyAssignmentError,
    ConstraintError,
)


@pytest.fixture(scope="module")
def model_for_test() -> PonyModel:
    model = PonyModel(provider="sqlite", filename=":memory:")
    return model


@pytest.fixture(scope="module")
def cat_model(model_for_test) -> PonyCategoryModel:
    return model_for_test.category_model


@pytest.fixture(scope="module")
def exp_model(model_for_test) -> PonyExpensesModel:
    return model_for_test.expenses_model


@pytest.fixture(scope="module")
def some_cats(cat_model):
    return [cat_model.add_category(f"Category {i}") for i in range(5)]


@pytest.fixture(scope="module")
def some_expenses(exp_model, some_cats):
    return [
        exp_model.add_expense(i, some_cats[1], comment=f"Expense {i}") for i in range(5)
    ]


@pytest.fixture(scope="module")
def not_delete_expense(exp_model, some_cats):
    return exp_model.add_expense(777, some_cats[3], comment="Expense wich we preserve")


@pytest.fixture(scope="module")
def cat_to_find(cat_model):
    return cat_model.add_category("Category for find test")


@pytest.fixture(scope="module")
def expenses_for_test(exp_model, cat_to_find):
    return [
        exp_model.add_expense(
            700700 + i,
            cat_to_find,
            expense_date=datetime(2000 + i, i + 1, i + 1, 12, 0),
            comment=f"Expense to find {i}",
        )
        for i in range(5)
    ]


@pytest.fixture(scope="function")
def cat_tree(cat_model):
    c0 = cat_model.add_category("ROOT")
    c05 = cat_model.add_category("semi root", parent=c0)
    c1 = [
        cat_model.add_category(f"child of ROOT num {i}", parent=c05) for i in range(5)
    ]
    c2 = [
        [
            cat_model.add_category(f"child of ROOT_num_{j} child num {i}", parent=c1[j])
            for i in range(5)
        ]
        for j in range(5)
    ]
    return (c0, c05, c1, c2)


class TestCategory:
    # While we are not mess everything up)
    def test_get_root_categories(self, cat_model, cat_tree):
        (c0, c05, c1, c2) = cat_tree
        root_cs = [cat_model.add_category(f"Root num. {i}") for i in range(5)]
        root_cs.append(c0)
        root_got = cat_model.get_root_categories()
        assert set(root_cs) == set(root_got)
        for rc in root_got:
            rc_cs = rc.get_children()
            if len(rc_cs) > 0:
                assert rc_cs[0] == c05

    def test_add_category(self, cat_model):
        c1 = cat_model.add_category("name")
        assert c1.name == "name"
        # assert c1.id == 1   # We don't know what is the default value pony use
        assert c1.id is not None
        assert c1.get_parent() is None

        c2 = cat_model.add_category("name2", parent=c1)
        assert c2.name == "name2"
        assert c2.get_parent() == c1

    def test_get_category_by_id(self, cat_model):
        c1 = cat_model.add_category("name")
        c2 = cat_model.get_category_by_id(c1.id)
        assert c1 == c2

    def test_get_categories_by_ids(self, cat_model, some_cats):
        cats2 = cat_model.get_categories_by_ids([c.id for c in some_cats])
        assert cats2 == some_cats

    def test_get_categories_by_ids_with_wrong_id(self, cat_model, some_cats):
        ids = [c.id for c in some_cats]
        for i in range(6):
            if i not in ids:
                ids.append(i)
                break
        with pytest.raises(NoDataError):
            cats2 = cat_model.get_categories_by_ids(ids)
        try:
            cats2 = cat_model.get_categories_by_ids(ids)
        except NoDataError as e:
            # we still can have at least some information
            cats2 = e.args[1]
            assert cats2 == some_cats

    def test_delete_category(self, cat_model):
        c1 = cat_model.add_category("name")
        c1id = c1.id
        (n1, n2) = c1.delete()
        assert c1.id is None
        assert c1.name == "DELETED"
        with pytest.raises(NoDataError):
            cat_model.get_category_by_id(c1id)
        assert n1 == 1
        assert n2 == 0

    def test_delete_category_with_children(self, cat_model, cat_tree):
        (c0, c05, c1, c2) = cat_tree
        c05id = c05.id
        (n1, n2) = c05.delete()
        assert c05.id is None
        assert c05.name == "DELETED"
        assert n1 == 31
        assert n2 == 0
        with pytest.raises(NoDataError):
            cat_model.get_category_by_id(c05id)
        allchildren = [*c1]
        for cc in c2:
            allchildren.extend(cc)
        for c in allchildren:
            with pytest.raises(NoDataError):
                cat_model.get_category_by_id(c.id)

    def test_delete_category_with_children_moved(self, cat_model, cat_tree):
        (c0, c05, c1, c2) = cat_tree
        c05id = c05.id
        (n1, n2) = c05.delete(CategoryDeletePolicy.move)
        assert c05.id is None
        assert c05.name == "DELETED"
        assert n1 == 6
        assert n2 == 0
        with pytest.raises(NoDataError):
            cat_model.get_category_by_id(c05id)
        for cc in c1:
            assert cc.get_parent() == c0
        for csofc, c in zip(c2, c1):
            for cofc in csofc:
                assert cofc.get_parent() == c

    def test_delete_category_with_children_and_exps(
        self, cat_model, cat_tree, exp_model
    ):
        (c0, c05, c1, c2) = cat_tree
        exp_ids = []
        for cs in c2:
            for c in cs:
                exp = exp_model.add_expense(100, c)
                exp_ids.append(exp.id)
        (n1, n2) = c05.delete(expense_handling=ExpensesHandlingPolicy.delete)
        assert c05.id is None
        assert c05.name == "DELETED"
        assert n1 == 31
        assert n2 == 25
        allchildren = [*c1]
        for cc in c2:
            allchildren.extend(cc)
        for c in allchildren:
            with pytest.raises(NoDataError):
                cat_model.get_category_by_id(c.id)
        for id in exp_ids:
            with pytest.raises(NoDataError):
                exp_model.get_expense_by_id(id)

    def test_delete_category_with_children_moved_exps(
        self, cat_model, cat_tree, exp_model
    ):
        (c0, c05, c1, c2) = cat_tree
        exp_ids = []
        for cs in c2:
            for c in cs:
                exp = exp_model.add_expense(100, c)
                exp_ids.append(exp.id)
        (n1, n2) = c05.delete(CategoryDeletePolicy.delete, ExpensesHandlingPolicy.move)
        assert c05.id is None
        assert c05.name == "DELETED"
        assert n1 == 31
        assert n2 == 25
        for id in exp_ids:
            assert c0 == exp_model.get_expense_by_id(id).get_category()

    def test_rename_category(self, cat_model):
        c = cat_model.add_category(name="name")
        c2 = cat_model.rename_category(c, "test")
        assert c2.name == "test"
        assert c.name == "test"
        assert c2 == c

    def test_rename_category_from_itself(self, cat_model):
        c = cat_model.add_category(name="name")
        c2 = c.rename("test")
        assert c2.name == "test"
        assert c.name == "test"
        assert c2 == c

    def test_get_parent(self, cat_model):
        c1 = cat_model.add_category("parent")
        c2 = cat_model.add_category("name", parent=c1)
        assert c2.get_parent() == c1

    def test_get_children(self, cat_model):
        c1 = cat_model.add_category("parent")
        children = [cat_model.add_category(f"child{i}", parent=c1) for i in range(5)]
        assert set(c1.get_children()) == set(children)


class TestExpense:
    def test_add_expense(self, exp_model, some_cats):
        timing1 = datetime.now()
        e1 = exp_model.add_expense(123, some_cats[0])  # basic addition
        timing2 = datetime.now()
        assert e1.amount == 123
        assert e1.get_category() == some_cats[0]
        assert e1.expense_date <= timing2 and e1.expense_date >= timing1
        assert e1.added_date <= timing2 and e1.added_date >= timing1
        assert e1.comment == ""

        timing1 = datetime.now()
        e2 = exp_model.add_expense(
            321,
            some_cats[1],
            datetime(2024, 4, 5, 15, 13),
            # datetime(2024, 4, 5, 15, 14, 12),
            "I love python",
        )  # full addition
        timing2 = datetime.now()
        assert e2.amount == 321
        assert e2.get_category() == some_cats[1]
        assert e2.expense_date == datetime(2024, 4, 5, 15, 13)
        # assert e2.added_date == datetime(2024, 4, 5, 15, 14, 12)
        assert e2.added_date <= timing2 and e2.added_date >= timing1
        assert e2.comment == "I love python"

    def test_delete_expense(self, exp_model, some_cats):
        e1 = exp_model.add_expense(123, some_cats[0])
        e1id = e1.id
        exp_model.delete_expense(e1)
        assert e1.id is None
        # assert e1.category is None
        assert e1.comment == "DELETED"
        with pytest.raises(NoDataError):
            exp_model.get_expense_by_id(e1id)

    def test_expense_self_delete(self, exp_model, some_cats):
        e1 = exp_model.add_expense(123, some_cats[0])
        e1id = e1.id
        e1.delete()
        assert e1.id is None
        # assert e1.category is None
        assert e1.comment == "DELETED"
        with pytest.raises(NoDataError):
            exp_model.get_expense_by_id(e1id)

    def test_get_expense_by_id(self, exp_model, not_delete_expense):
        ndeid = not_delete_expense.id
        assert exp_model.get_expense_by_id(ndeid) == not_delete_expense

    def test_get_expenses_by_ids(self, exp_model, some_expenses):
        ids = [exp.id for exp in some_expenses]
        exp_got = exp_model.get_expenses_by_ids(ids)
        assert set(some_expenses) == set(exp_got)

    def test_get_expenses_by_ids_fails(self, exp_model, some_expenses):
        ids = [e.id for e in some_expenses]
        for i in range(6):
            if i not in ids:
                ids.append(i)
                break
        with pytest.raises(NoDataError):
            exp_got = exp_model.get_expenses_by_ids(ids)
        try:
            exp_got = exp_model.get_expenses_by_ids(ids)
        except NoDataError as e:
            # we still can have at least some information
            exp_got = e.args[1]
            assert exp_got == some_expenses

    def test_set_attributes_from_expense(self, exp_model, some_cats):
        e1 = exp_model.add_expense(
            321,
            some_cats[1],
            # datetime(2024, 4, 5, 15, 13),
            datetime(2024, 4, 5, 15, 14, 12),
            "I love python",
        )  # full addition
        e1.set_attribute("amount", 1234)
        e1.set_attribute("category", some_cats[2])
        e1.set_attribute("expense_date", datetime(2023, 12, 13, 14, 4))
        # e1.set_attribute("added_date", datetime(2024, 1, 23, 15, 16))
        e1.set_attribute("comment", "Some other comment")
        # Check if attributes changed
        assert e1.amount == 1234
        assert e1.get_category() == some_cats[2]
        assert e1.expense_date == datetime(2023, 12, 13, 14, 4)
        # assert e1.added_date == datetime(2024, 1, 23, 15, 16)
        assert e1.comment == "Some other comment"
        # Check if them changed in DB
        e2 = exp_model.get_expense_by_id(e1.id)
        assert e2 == e1

    def test_set_attributes(self, exp_model, some_cats):
        e1 = exp_model.add_expense(
            321,
            some_cats[1],
            datetime(2024, 4, 5, 15, 13),
            # datetime(2024, 4, 5, 15, 14, 12),
            "I love python",
        )  # full addition
        # Multiple attr set
        exp_model.set_attributes(
            e1,
            {
                "amount": 12,
                "category": some_cats[3],
                # "added_date": datetime(2024, 3, 23, 15, 16),
                "expense_date": datetime(2024, 2, 27, 11, 46),
                "comment": "PYTHONNNNNN!",
            },
        )
        assert e1.amount == 12
        e1.get_category() == some_cats[3]
        e1.expense_date == datetime(2024, 2, 27, 11, 46)
        # e1.added_date == datetime(2024, 3, 23, 15, 16)
        e1.comment == "PYTHONNNNNN!"
        e3 = exp_model.get_expense_by_id(e1.id)
        assert e3 == e1

    def test_set_attributes_fails_with_id(self, exp_model, some_expenses, some_cats):
        with pytest.raises(PrimaryKeyAssignmentError):
            exp_model.set_attributes(
                some_expenses[1],
                {
                    "category": some_cats[2],
                    "expense_date": datetime(1999, 12, 23),
                    "id": 2,
                },
            )

    def test_validate_constrain(self, exp_model):
        right_constr = ExpenseConstraint(ExpenseField.amount, ConstraintType.geq, 12)
        right_constr2 = ExpenseConstraint(
            ExpenseField.comment, ConstraintType.equal, "s"
        )
        fail_constr = ExpenseConstraint(ExpenseField.comment, ConstraintType.leq, "s")
        fail_constr2 = ExpenseConstraint(ExpenseField.category, ConstraintType.leq, "s")
        assert exp_model._validate_constraint(right_constr) is True
        assert exp_model._validate_constraint(right_constr2) is True
        assert exp_model._validate_constraint(fail_constr) is False
        assert exp_model._validate_constraint(fail_constr2) is False

    def test_get_expenses_by_constraint_num(
        self, exp_model, expenses_for_test, some_cats
    ):
        # find one_arg with amount
        assert set(
            exp_model.get_expenses_by_constraints(
                [ExpenseConstraint(ExpenseField.amount, ConstraintType.geq, 700702)]
            )
        ) == set(expenses_for_test[2:])

        # find one_arg with expense_date
        assert set(
            exp_model.get_expenses_by_constraints(
                [
                    ExpenseConstraint(
                        ExpenseField.expense_date,
                        ConstraintType.less,
                        datetime(2000 + 3, 3 + 1, 3 + 1, 12, 0),
                    )
                ]
            )
        ) == set(expenses_for_test[0:3])
        assert set(
            exp_model.get_expenses_by_constraints(
                [
                    ExpenseConstraint(
                        ExpenseField.expense_date,
                        ConstraintType.leq,
                        datetime(2000 + 3, 3 + 1, 3 + 1, 12, 0),
                    )
                ]
            )
        ) == set(expenses_for_test[0:4])

    def test_get_expenses_by_constraint_comment(self, exp_model, expenses_for_test):
        # find one_arg with comment
        assert set(
            exp_model.get_expenses_by_constraints(
                [
                    ExpenseConstraint(
                        ExpenseField.comment, ConstraintType.equal, "Expense to find 2"
                    )
                ]
            )
        ) == set([expenses_for_test[2]])

    def test_get_expenses_by_constraint_comment_fails(
        self, exp_model, expenses_for_test
    ):
        # find one_arg >= comment
        with pytest.raises(ConstraintError):
            exp_model.get_expenses_by_constraints(
                [
                    ExpenseConstraint(
                        ExpenseField.comment, ConstraintType.geq, "Expense to find 2"
                    )
                ]
            )

    def test_get_expenses_by_constraint_category(
        self, exp_model, expenses_for_test, cat_to_find
    ):
        # find one_arg with category
        assert set(
            exp_model.get_expenses_by_constraints(
                [
                    ExpenseConstraint(
                        ExpenseField.category, ConstraintType.equal, cat_to_find
                    )
                ]
            )
        ) == set(expenses_for_test)

    def test_get_expenses_by_constraint_category_fails(
        self, exp_model, expenses_for_test, cat_to_find
    ):
        # find one_arg <= category
        with pytest.raises(ConstraintError):
            exp_model.get_expenses_by_constraints(
                [
                    ExpenseConstraint(
                        ExpenseField.category, ConstraintType.leq, cat_to_find
                    )
                ]
            )

    def test_get_expenses_by_constraint_many(
        self, exp_model, expenses_for_test, cat_to_find
    ):
        # find many_args with amount and category
        assert set(
            exp_model.get_expenses_by_constraints(
                [
                    ExpenseConstraint(ExpenseField.amount, ConstraintType.less, 800000),
                    ExpenseConstraint(
                        ExpenseField.category, ConstraintType.equal, cat_to_find
                    ),
                ]
            )
        ) == set(expenses_for_test)

    def test_get_expense_amount_by_time_period(
            self, exp_model, expenses_for_test
    ):
        assert exp_model.get_expense_amount_by_time_period(
            datetime(2000, 1, 1, 12, 0), datetime(2002, 3, 3, 12, 0)
        ) == 700700*3 + 3

    # def test_get_parent(self, cat_model):
    #     c1 = cat_model.add_category('parent')
    #     c2 = cat_model.add_category('name', parent=c1)
    #     assert c2.get_parent() == c1

    # def test_get_children(self, cat_model):
    #     c1 = cat_model.add_category('parent')
    #     children = [cat_model.add_category(f"child{i}", parent=c1) for i in range(5)]
    #     assert set(c1.get_children()) == set(children)
