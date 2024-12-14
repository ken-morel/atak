"""Just a login page."""
from taktk.component import component
from taktk.dictionary import Dictionary
from taktk.menu import Menu
from taktk.notification import Notification
from ttkbootstrap import Window


@component
def Signin(self):
    r"""
    \frame padding=100
        \frame pos:pack pos:fill=BOTH
            \frame pos:pack pos:fill=BOTH padding=20
                \label text=[label.name] pos:pack=LEFT\
                    font='"Nova Square" 15'
                \entry text={{username||username = value}}\
                    pos:pack=RIGHT width=30 font='"Nova Square" 18'
            \frame pos:pack pos:fill=BOTH padding=20
                \label text=[label.password] pos:pack=LEFT\
                    font='"Nova Square" 15'
                \entry show='*' text={$password}\
                    pos:pack=RIGHT width=30 font='"Nova Square" 18'
        \frame pos:pack pos:fill=BOTH
            \button command={lambda: None} text=[gt_signup] pos:pack=LEFT
            \button command={signin} text=[submit] pos:pack=RIGHT
    """
    username = ""
    password = ""

    def signin():
        name = self["username"]
        password = self["password"]
        Notification(
            "Todos",
            f"Signin successful({name=!r}, {password=!r})",
            bootstyle="info",
            duration=5000,
        ).show()

    return locals()


english = Dictionary(
    {
        "label": {
            "name": "Name: ",
            "password": "Password: ",
        },
        "gt_signup": "< Signup",
        "submit": "Signin >",
        "popup": {
            "theme": {
                "__label__": "Theme",
                "dark": "Dark",
                "dark-blue": "Dark Blue",
                "light": "Light",
                "light-blue": "Light Blue",
            },
            "lang": {
                "__label__": "Language",
                "fr": "francais",
                "en": "english",
            },
        },
    }
)
french = Dictionary(
    {
        "label": {
            "name": "Nom: ",
            "password": "Mot De passe: ",
        },
        "gt_signup": "< S'Enregistrer",
        "submit": "Se connecter >",
        "popup": {
            "theme": {
                "__label__": "Theme",
                "dark": "Sombre",
                "dark-blue": "Bleu Sombre",
                "light": "Claire",
                "light-blue": "Bleu Clair",
            },
            "lang": {
                "__label__": "Langue",
                "fr": "francais",
                "en": "english",
            },
        },
    }
)


def theme_setter(name):
    """Create a function to set theme."""

    def setter():
        root.style.theme_use(name)
        # cosmo,flatly,litera,minty,lumen,sandstone,yeti,pulse,united,morph,
        # journal,darkly,superhero,solar,cyborg,vapor,simplex,cerculean

    return setter


english.install()
menu = Menu(
    {
        "@theme": {
            "@light": theme_setter("cosmo"),
            "@light-blue": theme_setter("morph"),
            "@dark": theme_setter("darkly"),
            "@dark-blue": theme_setter("superhero"),
        },
        "@lang": {
            "@en": lambda: (english.install(), update()),
            "@fr": lambda: (french.install(), update()),
        },
    },
    translations="popup",
)


def update():
    """Update the component."""
    Signin().render(root).grid(column=0, row=0, sticky="nsew")


root = Window()
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
menu.toplevel(root)
Signin().render(root).grid(column=0, row=0, sticky="nsew")
root.mainloop()
