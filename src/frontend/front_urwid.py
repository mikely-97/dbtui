from __future__ import annotations
from typing import Iterable

buttons_1_txt = ["alpha", "beta", "gamma"]
buttons_2_txt = ["prima", "secunda", "tertia"]
buttons_3_txt = ["one", "two", "three"]

import urwid as u

def keyhint_constructor(hotkey: str, label: str) -> u.Filler:
    
    text_label = ': '.join([hotkey, label])
    # TODO: decide if we need text or a button
    keyhint = u.Text(text_label)
    integrated = u.Filler(keyhint)
    return integrated

def keyhint_row_constructor(*keyhints_text: tuple[str, str]) -> u.Columns:

    return u.Columns([keyhint_constructor(*keyhint) for keyhint in keyhints_text])

def standard_view_handler():
    pass


def handler(size: tuple[()] | tuple[int] | tuple[int, int], key: str) -> str | None:
    pass

def standard_view(model=None, focus:str='model'):
    common_actions: u.Columns = keyhint_row_constructor(
        ('F1', 'Options'),
        ('F', 'Search'),
        ('q', 'Close')
    )

    # TODO: use dbtui API to get parents
    parents = [u.Button(i) for i in buttons_1_txt]
    parents_actions: u.Columns = keyhint_row_constructor(
        ('F2', "show paths/names"),
        ('S', "open in split with current"),
    )
    parents_column = u.LineBox(u.ListBox(parents), title='parents')
    # TODO: use dbtui API to get model data
    lorem = open('src/frontend/lorem.txt', 'r').read()
    model_box = u.ScrollBar(u.Scrollable(
        u.Text(lorem)
    ))
    model_actions: u.Columns = keyhint_row_constructor(
        ('e', 'edit in dbtui'),
        ('E', 'edit externally'),
        ('p', 'model properties'),
    )
    model_column = ('weight', 3, u.LineBox(model_box, title='model'))
    # TODO: use dbtui API to get children data
    children = [u.Button(i) for i in buttons_2_txt]
    children_actions: u.Columns = keyhint_row_constructor(
        ('F2', "show paths/names"),
        ('S', "open in split with current"),
    )
    children_column = u.LineBox(u.ListBox(children), title='children')
    children_column.keypress = handler

    columns = u.Columns([parents_column, model_column, children_column])

    result = u.Pile([
        ('weight', 20, columns), 
        common_actions,
        model_actions
    ])
    return result




loop = u.MainLoop(standard_view())
#loop = urwid.MainLoop(keyhints_container)
#loop = urwid.MainLoop(keyhints[0])
loop.run()
