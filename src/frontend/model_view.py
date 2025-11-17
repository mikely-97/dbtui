from typing import Literal

from textual import widgets, containers, screen

from .common import ModelList, ModelListItem

isolated = True
if isolated:
    from .pseudo import DbtProject, DbtModel
else:
    from ..backend.project import DbtProject, DbtModel


class ModelRelativesList(ModelList):
    
    def on_list_view_highlighted(self, event: widgets.ListView.Highlighted) -> None:
        list_item: ModelListItem = event.item
        pass 

    def on_list_view_selected(self, event: widgets.ListView.Selected) -> None: 
        list_item: ModelListItem = event.item 
        dbt_model = list_item.dbt_model
        assert isinstance(dbt_model, DbtModel)
        self.app.ctx['active_model'] = dbt_model
        self.screen.on_model_change()
    
    def on_model_change(self, relatives_type: Literal['parents', 'children']):
        model: DbtModel = self.app.ctx['active_model']
        if relatives_type == 'parents':
            self.populate_with_models(model.parents())
        elif relatives_type == 'children':
            self.populate_with_models(model.children())
        else:
            raise NotImplementedError


class ModelView(screen.Screen):


    BINDINGS = [
        # ("O", "options", "open options"),
        ("f", "push_screen('model_search')", "search models"),
    ]

    def compose(self):
        yield containers.ScrollableContainer(
            widgets.TextArea(
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
            widgets.TextArea(
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
        assert isinstance(model_content, widgets.TextArea)
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

