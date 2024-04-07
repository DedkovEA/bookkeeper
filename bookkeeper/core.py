from enum import Enum


class CategoryDeletePolicy(Enum):
    """
    Class for chosing what to do with children of deleted category
    delete - delete all children recursively
    move - move all children to deleted category parent
    """
    delete: int = 0
    move: int = 1


class ExpensesHandlingPolicy(Enum):
    """
    Class for chosing what to do with children of deleted category
    delete - delete all expenses in category
    move - move all expenses to category parent
    """
    delete: int = 0
    move: int = 1
