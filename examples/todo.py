from dataclasses import dataclass
from tkinter import Tk

from taktk.component import Component


@dataclass
class TodoItem:
    desc: str
    done: bool = False


class Todo(Component):
    r"""
    \frame
        \frame pos:grid=0,0 width=350 pos:sticky='nsew'
            \entry width=50 pos:grid=0,0 text={{entry}} pos:xweight=2
            \button text='+' command={add_todo} pos:grid=1,0 pos:xweight=0
        \frame pos:grid=0,1 width=350 pos:sticky='nsew'
            !enum todos:(idx, todo)
                {fg = "#8a8" if todo.done else "#f88"}
                \label foreground={fg} \
                      text={str(idx + 1) + ') ' + todo.desc} \
                      pos:grid={(0, idx)} pos:sticky='nsw' \
                      bind:1={toggler(idx)}
                # popper closure does popping for you
                \button text={'mark done' if not todo.done else 'mark undone'}\
                       command={toggler(idx)} pos:grid={(1, idx)}\
                       pos:sticky='nse'
                \button text='remove' command={popper(idx)}\
                       pos:grid={(2, idx)} pos:sticky='nse'
    """

    todos = [TodoItem("a", True), TodoItem("b", False)]
    entry = "Enter todo here"

    def close(self):
        root.destroy()

    def add_todo(self):
        self.todos.append(TodoItem(desc=self["entry"]))
        self.entry = ""
        self.update()

    def clear(self):
        self.todos.clear()
        self.update()

    def popper(self, idx):
        def func(*_):
            self.todos.pop(idx)
            self.update()

        return func

    def toggler(self, idx):
        def func(*_):
            self.todos[idx].done = not self.todos[idx].done
            self.update()

        return func


root = Tk()
root.title("Todo list")

Todo().render(root).grid(column=0, row=0)

root.mainloop()
