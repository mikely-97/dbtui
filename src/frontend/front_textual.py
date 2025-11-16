
from textual.app import App 
from textual import widgets
from typing import Any 

isolated = True

if isolated:
    from pseudo import DbtProject, DbtModel
else:
    from ..backend.project import DbtProject, DbtModel

from model_search import ModelSearch
from model_view import ModelView



class dbtuiFrontend(App):

    ctx: dict[str, Any]

    BINDINGS = [
        # ("O", "options", "open options"),
        ("f", "push_screen('model_search')", "search models"),

    ]

    SCREENS = {
        'model_search': ModelSearch,
        'model_view': ModelView,
        }

    def load_context(self):
        # TODO: context should be its own dataclass
        if not isolated:
            raise NotImplementedError
        self.ctx: dict[str, Any] = dict()
        self.ctx['project']: DbtProject = DbtProject('ISOLATED')
        # self.ctx['active_model'] = None 
        self.ctx['active_model']: DbtModel = DbtModel.generate_random() 


    def compose(self):
        assert isolated # TODO: choose the initial screen based on dbtui cache
        yield widgets.Footer()
        # yield ModelSearch(id='model_search')
    

    def on_mount(self):
        self.load_context()
        # self.push_screen('model_search')
        self.push_screen('model_view')

if __name__ == '__main__':

    dbtui_front = dbtuiFrontend()
    dbtuiFrontend().run()
