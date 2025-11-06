
from textual.app import App, ComposeResult
from textual import widgets as w
from textual import containers
import random
import uuid

isolated = True

lorem = open('src/frontend/lorem.txt', 'r').read()

def get_children(model_name: str) -> str:
    # TODO: properly get children of a model
    assert isolated
    number_of_children = random.randint(0, 8)
    return [str(uuid.uuid4()) for _ in range(number_of_children)]


def get_parents(model_name: str) -> str:
    # TODO: properly get parents of a model
    assert isolated
    number_of_parents = random.randint(0, 8)
    return [str(uuid.uuid4()) for _ in range(number_of_parents)]

def load_model_text(model_name: str) -> str:
    # TODO: properly get model's text
    assert isolated
    return lorem

def switch_model(called: w.Button):
    pass

def standard_view(model_name: str):
    parents_buttons = [w.Button()]

class ModelListItem(ListItem):

    def compose(self):
        pass

class ParentsList(ListView):
    
    def compose(self) -> ComposeResult:
        assert isolated
        model_name = str(uuid.uuid4())
        pass


class StandardView(containers.Horizontal):
    
    def compose(self) -> ComposeResult:
        assert isolated
        model_name = str(uuid.uuid4())
        yield w.ListView(
                *[
                    w.ListItem(
                        w.Label(parent)
                    )
                    for parent in get_parents(model_name=model_name)
                ],
                name='parents',
            )
        yield containers.VerticalScroll(
                w.Markdown(
                    load_model_text(model_name=model_name),
                    name='model',
                )
            )
        yield w.ListView(
                *[
                    w.ListItem(
                        w.Label(child)
                    )
                    for child in get_children(model_name=model_name)
                ],
                name='children',
            )



class dbtuiFrontend(App):

    BINDINGS = [
        ("O", "options", "open options")
    ]

    def compose(self):

        yield StandardView()
        yield w.Footer()

    def action_options(self) -> None:
        raise

if __name__ == '__main__':
    dbtuiFrontend().run()
