from builtins import _

import taktk
import taktk.application
import taktk.component
import taktk.dictionary
import taktk.menu
import taktk.notification

from . import pages
from .admin import DIR

recent_files = ["ama.py", "test.py", "ttkbootstrap.py", "label.py"]


class Application(taktk.application.Application):
    def __init__(self):
        super().__init__(
            icon="@icon",
            dictionaries=DIR / "dictionaries",
            media_path=DIR / "media",
            params=dict(
                themename="darkly",
                minsize=(800, 400),
            ),
            address=("", 56789),
            menu=taktk.make_menu(
                {
                    "@file": {
                        "@open": lambda: None,
                        "!sep": None,
                        "@/menu.quit": exit,
                    },
                    "@preferences": {
                        "@language": {},
                    },
                    "@quit": exit,
                },
                translations="menu",
            ),
            store=(
                DIR / "store.json",
                {
                    "language": "english",
                    "theme": "darkly",
                },
            ),
            pages=pages,
            layout=Layout(self),
        )

    def init(self):
        self.menu["@preferences/@language"] = {
            lang: self.dictionaries.get(lang).install
            for lang in self.dictionaries.languages
        }
        style = self.root.style
        self.menu["@preferences/@theme"] = {
            t: lambda s=self.set_theme, t=t: s(t) for t in style.theme_names()
        }
        try:
            self.root.style.theme_use(self.store["theme"])
        except Exception as e:
            print(e)
        self.menu.update()
        self.set_language(self.store["language"])
        taktk.dictionary.Dictionary.subscribe(self.update_language)

    def set_theme(self, theme):
        self.root.style.theme_use(theme)
        self.store["theme"] = theme
        taktk.notify(
            "Todos",
            _("preferences.success_modified"),
            bootstyle="info",
            duration=10000,
        )

    def back(self):
        self.view.back()

    def forward(self):
        self.view.forward()

    def update_language(self):
        self.store["language"] = taktk.Dictionary.dictionary.language
        self.store.save()
        Notification(
            "Todos",
            _("preferences.success_modified"),
            bootstyle="info",
            duration=10000,
        ).show()


@component
def Layout(self):
    r"""
    \frame weight:x='0: 10' weight:y='1: 10, 2: 10'
        \frame padding=5 weight:y='2:10' weight:x='4:10' pos:grid=0,0 pos:sticky='nsew'
            \button command={back}    image=img:@backward{width: 20} pos:grid=0,0 pos:sticky='w' bootstyle='dark outline'
            \button command={gt_users}    image=img:@users-between-lines{height: 20} pos:grid=1,0 pos:sticky='w' bootstyle='dark outline'
            \button command={gt_todos}    image=img:@check-double{height: 20} pos:grid=2,0 pos:sticky='w' bootstyle='dark outline'
            \label text={f'logged in as: {User.current().name}' if User.current() else "not logged in!"} pos:grid=3,0
            \button command={forward} image=img:@forward{width: 20}  pos:grid=5,0 pos:sticky='e' bootstyle='dark outline'
        \frame:outlet pos:grid=0,1
    """
    user = None

    def back():
        taktk.application.back()

    def forward():
        taktk.application.forward()

    def gt_users():
        taktk.application("users")

    def gt_todos():
        taktk.application("todos")

    return locals() | globals()
