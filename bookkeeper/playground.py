from bookkeeper.view.pyside_gui_view.gui_view import GUI_Based_View
from bookkeeper.view.view_data import ViewExpense, ViewCategory


g = GUI_Based_View()
test_exps = [ViewExpense(0, "123", "Milk", "21/02/2024", "Yammy!"),
             ViewExpense(1, "183,44", "Book", "14/03/2024", "Not yammy!"),
             ViewExpense(2, "66,99", "Candies", "01/01/2024", "Yammy x10!")]
test_exps2 = [ViewExpense(3, "123", "Milk", "21/02/2024", "Yammy!"),
             ViewExpense(0, "183,44", "Book", "14/03/2024", "Not yammy!"),
             ViewExpense(4, "66,99", "Candies", "01/01/2024", "Yammy x10!")]
g.refresh_expenses_table(test_exps)
g.refresh_expenses_table(test_exps2)
g.remove_expenses([ViewExpense(0, *[""]*4)])
# g.remove_expenses([ViewExpense(6, *[""]*4)])
g.central_widget.expense_add_widget.category_selection.add_category(ViewCategory(0, "root"))
g.central_widget.expense_add_widget.category_selection.add_category(ViewCategory(1, "root2"))
g.central_widget.expense_add_widget.category_selection.add_category(ViewCategory(2, "child", 0))
g.central_widget.expense_add_widget.category_selection.add_category(ViewCategory(3, "child2", 0))
g.central_widget.expense_add_widget.category_selection.refresh_categories_list(
    [ViewCategory(2, "child 1 of 1", 0),
     ViewCategory(3, "child 2 of 2", 5),
     ViewCategory(4, "child 1 of child 1 of 2", 6),
     ViewCategory(0, "root 1"),
     ViewCategory(6, "child 1 of 2", 5),
     ViewCategory(5, "root 2", None)])
print(g.central_widget.expense_add_widget.category_selection.update_category(ViewCategory(6, "new root from ch1of2")))
print(g.central_widget.expense_add_widget.category_selection.update_category(ViewCategory(6, "back from root to r2", 5)))
g.remove_categories([ViewCategory(6, "child 1 of 1", 0)])
try:
    g.remove_categories([ViewCategory(6, "child 1 of 1", 0), 
                     ViewCategory(4, "child 2 of 2", 5)])
except Exception:
    pass
def add_hndlr(name: str, parent = None) -> None:
    print(f"Create category with name=\"{name}\" and parent={parent}")
g.central_widget.expense_add_widget.category_selection.register_category_add_handler(add_hndlr)
g.start()
