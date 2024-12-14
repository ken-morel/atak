from dataclasses import dataclass
from functools import cache

from taktk.component import Component
from taktk.menu import Menu
from taktk.notification import Notification
from taktk.page import Redirect
from taktk.writeable import NamespaceWriteable

from ..admin import Todo as Todo
from ..admin import User

store = STORE = None


class TodoPage(Component):
    r"""
    \frame padding=20
        \frame pos:grid=0,0 pos:sticky='nsew'
            \entry width=80 pos:grid=0,0 text={{entry}} pos:sticky='nsw' bind:Key-Return={add_todo}
            \button text='+' command={add_todo} pos:grid=1,0 pos:sticky='nse'
        \frame pos:grid=0,1 pos:sticky='nsew'
            !enum todos:(idx, todo)
                \label bootstyle={'info' if todo.done else 'danger'} text={str(idx + 1) + ') ' + todo.desc} pos:grid={(0, idx)} pos:xweight=10 pos:sticky='nswe' bind:1={toggler(todo.uuid)} bind:3={popup_menu(todo.uuid)}
                \button text={_('pages.todos.mark-done') if not todo.done else _('pages.todos.mark-undone')} command={toggler(todo.uuid)} pos:grid={(1, idx)} pos:sticky='nse'
                \button text=[pages.todos.remove] command={popper(todo.uuid)} pos:grid={(2, idx)} pos:sticky='nse'
    """

    def __init__(self, user, entry):
        self.user = user
        self.entry = entry
        super().__init__()

    def init(self):
        self["todos"] = Todo.for_user(self.user)
        NamespaceWriteable(self.namespace, "entry").subscribe(
            self.update_entry
        )

    def update_entry(self):
        store['entry'] = self["entry"]

    def close(self):
        root.destroy()

    def add_todo(self, *_):
        if not self["entry"].strip():
            return Notification(
                "Empty field",
                "Please, enter an item",
                duration=1000,
                bootstyle="warning",
                source="todo-empty-notification",
            ).show()
        self["user"].create_todo(self["entry"]).save()
        self["entry"] = ""
        self.update()

    def popper(self, uuid):
        def func(*_):
            Todo.from_uuid(uuid).delete()
            self.update()

        return func

    def toggler(self, uuid):
        def func(*_):
            obj = Todo.from_uuid(uuid)
            obj.done = not obj.done
            obj.save()
            self.update()

        return func

    def update(self):
        self["todos"] = Todo.for_user(self.user)
        super().update()

    def popup_menu(self, uuid):
        menu = Menu(
            {
                "@toggle": self.toggler(uuid),
                "@remove": self.popper(uuid),
                "@edit": self.editer(uuid),
            },
            translations="pages.todos.menu",
        )

        def func(e):
            menu.post(e.x_root, e.y_root)

        return func

    def editer(self, uuid):
        def edit(*_):
            from customtkinter import CTkInputDialog

            value = CTkInputDialog(
                text="Enter the new value", title="Todos"
            ).get_input()
            todo = Todo.from_uuid(uuid)
            todo.desc = value
            todo.save()
            self.update()

        return edit


@cache
def default(_store, /):
    global store, STORE, user
    STORE = _store
    if User.is_login():
        user = User.current()
        store = STORE.for_page(__name__).partition(user.name, {
            "entry": _("pages.todos.placeholder"),
        })
        return TodoPage(user=user, entry=store['entry'])
    else:
        raise Redirect("sign@signin")
