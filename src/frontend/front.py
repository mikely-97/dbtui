from __future__ import annotations

buttons_1_txt = ["alpha", "beta", "gamma"]
buttons_2_txt = ["prima", "secunda", "tertia"]
buttons_3_txt = ["one", "two", "three"]

import urwid
import urwid as u

buttons_1 = [urwid.Button(i) for i in buttons_1_txt]
buttons_2 = [urwid.Button(i) for i in buttons_2_txt]
buttons_3 = [urwid.Button(i) for i in buttons_3_txt]



menu_1 = urwid.ListBox(buttons_1)
menu_2 = urwid.ListBox(buttons_2)
menu_3 = urwid.ListBox(buttons_3)

lorem = open('src/frontend/lorem.txt', 'r').read()

txt = urwid.Text(lorem)

columns = urwid.Columns(
    [
        urwid.LineBox(menu_1, title='ancestors'),
        # urwid.LineBox(menu_2, title='model'),
        # urwid.LineBox(txt, title='model'),
        # urwid.LineBox(urwid.ListBox(txt), title='model'),
        urwid.LineBox(u.ScrollBar(urwid.Scrollable(txt)), title='model'),
        urwid.LineBox(menu_3, title='children'),
    ]
)

loop = urwid.MainLoop(columns)
loop.run()
