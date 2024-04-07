import os

from bookkeeper.view.pyside_gui_view.gui_view import GUI_Based_View
from bookkeeper.models.pony_models.pony_model import PonyModel
from bookkeeper.presenter import Presenter


gui_view = GUI_Based_View()

# check if necessary directory exists
cur_dir = os.path.dirname(os.path.abspath(__file__))
appdata_dir = os.path.join(cur_dir, "appdata")
if not os.path.isdir(appdata_dir):
    os.mkdir(appdata_dir)

pony_model = PonyModel(
    provider="sqlite",
    # filename=str(current_dir)+"\\appdata\\bookkeeper.sqlite",
    filename="../../appdata/bookkeeper.sqlite",
    create_db=True
)

p = Presenter(gui_view, pony_model)
