
from textual.app import App, ComposeResult
from textual import events, widgets as w
from textual import containers
from textual.screen import Screen
from typing import Any, Self, Iterable, Literal

isolated = True

if isolated:
    from pseudo import DbtProject, DbtModel
else:
    from ..dbtui.project import DbtProject, DbtModel



w.ListItem()

class ModelListItem(w.ListItem):

    dbt_model: DbtModel

    def __init__(self, model: DbtModel, **kwargs):

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

    def populate_with_models(self, models: Iterable[DbtModel]):
        self.clear()
        for model in models:
            self.append(
                ModelListItem(
                    model=model
                )
            )


class ModelSearchList(ModelList):

    def on_list_view_highlighted(self, event: w.ListView.Highlighted) -> None:
        list_item: ModelListItem = event.item
        model_preview = self.screen.get_widget_by_id('model_preview')
        assert isinstance(model_preview, w.TextArea)
        model_preview.clear()
        model_preview.text = list_item.dbt_model.text

class ModelRelativesList(ModelList):
    
    def on_list_view_highlighted(self, event: w.ListView.Highlighted) -> None:
        list_item: ModelListItem = event.item
    
    def on_model_change(self, relatives_type: Literal['parents', 'children']):
        model: DbtModel = self.app.ctx['active_model']
        if relatives_type == 'parents':
            self.populate_with_models(model.parents())
        elif relatives_type == 'children':
            self.populate_with_models(model.children())
        else:
            raise NotImplementedError
            


class ModelSearchInput(w.Input):
    
    def on_input_changed(self, message: w.Input.Changed):
        assert isinstance(self.app, dbtuiFrontend)
        assert isinstance(self.app.ctx['project'], DbtProject)
        models = self.app.ctx['project'].search_model(message.value)
        model_list = self.screen.get_widget_by_id('model_list')
        assert isinstance(model_list, ModelSearchList)
        model_list.populate_with_models(models=models)



class ModelSearch(Screen):

    BINDINGS = [
        ("O", "options", "open options")
    ]

    def compose(self):
        
        yield containers.Horizontal(
            ModelSearchList(
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


class ModelView(Screen):


    BINDINGS = [
        # ("O", "options", "open options"),
        ("f", "push_screen('model_search')", "search models"),
    ]

    def compose(self):
        yield containers.ScrollableContainer(
            w.TextArea(
                id='model_content',
                name='content',
                read_only=True, # TODO: not read-only when pressing Enter, back to read-only when pressing Esc 
                show_line_numbers=True,
                language='sql',
            ),
        )
        yield containers.Horizontal(
            ModelRelativesList(
                id='parents',
                name='model_parents',
            ),
            w.TextArea(
                id='model_properties',
                name='model properties',
                read_only=True,
            ),
            ModelRelativesList(
                id='children',
                name='model children',
            )
        )
    
    def on_model_change(self):
        model: DbtModel = self.app.ctx['active_model']
        # model_content
        model_content = self.get_widget_by_id('model_content')
        assert isinstance(model_content, w.TextArea)
        model_content.clear()
        model_content.text = model.text
        # parents
        parents = self.get_widget_by_id('parents')
        assert isinstance(parents, ModelRelativesList)
        parents.on_model_change('parents')
        # children
        children = self.get_widget_by_id('children')
        assert isinstance(children, ModelRelativesList)
        children.on_model_change('children')
        # TODO: model properties
        pass

    def on_mount(self):
        if self.app.ctx['active_model'] is None:
            self.app.push_screen('model_search')
        assert isinstance(self.app.ctx['active_model'], DbtModel)
        self.on_model_change()   


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
        yield w.Footer()
        # yield ModelSearch(id='model_search')
    

    def on_mount(self):
        self.load_context()
        # self.push_screen('model_search')
        self.push_screen('model_view')

if __name__ == '__main__':

    dbtui_front = dbtuiFrontend()

    

    dbtuiFrontend().run()
