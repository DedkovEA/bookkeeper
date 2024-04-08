class PrimaryKeyAssignmentError(AttributeError):
    ...


class NoDataError(Exception):
    ...


class ConstraintError(TypeError):
    ...


class GUIError(Exception):
    ...


class GUIInsertionError(GUIError):
    ...


class GUIUpdateError(GUIError):
    ...


class GUIRemoveError(GUIError):
    ...


class NoAccessError(Exception):
    ...


class NoAccessToGenericValuesError(NoAccessError):
    ...
