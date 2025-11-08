
from textual.app import App, ComposeResult
from textual import events, widgets as w
from textual import containers
from textual.screen import Screen
from typing import Any, Self, Iterable
import random
import uuid

isolated = True

lorem = open('src/frontend/lorem.txt', 'r').read()

def rand_uuid() -> str:

    raw = uuid.uuid4()
    return raw.urn

class PseudoModel:
    name: str 
    filepath: str
    text: str

    def __init__(self, name, filepath):
        self.name = name 
        self.filepath = filepath
        self.text = lorem
    
    @classmethod
    def generate_random(cls):
        return cls(
            name=rand_uuid(),
            filepath= "/".join([
                rand_uuid(),
                rand_uuid()
            ])
        )

    def ancestors(self) -> list[Self]:
        result = []
        for _ in range(random.randint(2, 5)):
            result.append(self.generate_random())
        return result

    def children(self) -> list[Self]:
        result = []
        for _ in range(random.randint(2, 5)):
            result.append(self.generate_random())
        return result

    
class PseudoProject:
    name: str
    #models: list[PseudoModel]

    def __init__(self, name):
        self.name = name

    def search_model(self, query) -> list[PseudoModel]:
        result = []
        for _ in range(random.randint(2,5)):
            result.append(PseudoModel.generate_random())
        return result
    
    def get_model_by_filepath(self, filapath: str) -> PseudoModel:
        return PseudoModel.generate_random()

    def get_model_by_name(self, name: str) -> PseudoModel:
        return PseudoModel.generate_random()



w.ListItem()

class ModelListItem(w.ListItem):

    dbt_model: PseudoModel

    def __init__(self, model: PseudoModel, **kwargs):

        super().__init__(
            containers.VerticalGroup(
                w.Label(model.name),
                w.Rule(),
                w.Label(model.filepath),
            ),
            **kwargs
        )
        self.dbt_model = model
    

class ModelList(w.ListView):

    def populate_with_models(self, models: Iterable[PseudoModel]):
        self.clear()
        for model in models:
            self.append(
                ModelListItem(
                    model=model
                )
            )

    def on_list_view_highlighted(self, event: w.ListView.Highlighted) -> None:
        list_item: ModelListItem = event.item
        model_preview = self.screen.get_widget_by_id('model_preview')
        assert isinstance(model_preview, w.TextArea)
        model_preview.clear()
        model_preview.text = list_item.dbt_model.text
        # assert 1 == list_item.dbt_model.text
        

class ModelSearchInput(w.Input):
    
    def on_input_changed(self, message: w.Input.Changed):
        assert isinstance(self.app, dbtuiFrontend)
        assert isinstance(self.app.ctx['project'], PseudoProject)
        models = self.app.ctx['project'].search_model(message.value)
        model_list = self.screen.get_widget_by_id('model_list')
        assert isinstance(model_list, ModelList)
        model_list.populate_with_models(models=models)



class ModelSearch(Screen):

    BINDINGS = [
        ("O", "options", "open options")
    ]

    def compose(self):
        
        yield containers.Horizontal(
            ModelList(
                #w.Placeholder,
                id='model_list',
                name='model list'
                ),
            containers.ScrollableContainer(
                w.TextArea(
                    id='model_preview',
                    name='preview',
                    read_only=True,
                    show_line_numbers=True,
                    language='sql'
                ),
                id='model_preview_scrollable'
            ),
            id='search_results'
        )
        yield ModelSearchInput(
            id='search_input',
            placeholder='Enter the model name or dbt search string'
            
        )
    
    def on_mount(self):
        self.app.set_focus(
            self.get_widget_by_id('search_input')
        )


        


class dbtuiFrontend(App):

    ctx: dict[str, Any]

    BINDINGS = [
        # ("O", "options", "open options"),
        ("ctrl+f", "push_screen('model_search')", "search models"),

    ]

    SCREENS = {'model_search': ModelSearch}

    def load_context(self):
        # TODO: context should be its own dataclass
        if not isolated:
            raise NotImplementedError
        self.ctx: dict[str, Any] = dict()
        self.ctx['project'] = PseudoProject('ISOLATED')
        self.ctx['model'] = None 


    def compose(self):
        assert isolated # TODO: choose the initial screen based on dbtui cache
        yield w.Footer()
        # yield ModelSearch(id='model_search')
    

    def on_mount(self):
        self.load_context()
        self.push_screen('model_search')

if __name__ == '__main__':

    dbtui_front = dbtuiFrontend()

    

    dbtuiFrontend().run()
