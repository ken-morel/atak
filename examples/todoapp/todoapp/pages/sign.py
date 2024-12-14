import taktk
from taktk.component import Component
from taktk.notification import Notification

from ..admin import User


class Signin(Component):
    r"""
    \frame weight:x='0: 1' weight:y='0: 1' padding=50
        \frame pos:grid=0,0 weight:x='0:1'
            \frame pos:grid=0,0 padding=20 weight:x='0:1' weight:y='0:1' pos:sticky='nswe'
                \label text=[pages.signin.label.name] pos:grid=0,0 pos:sticky='w' font='"Nova Square" 15'
                \entry text={{username}} font='"Nova Square" 18' pos:grid=1,0 width=30 pos:sticky='e'
            \frame pos:grid=0,1 padding=20 weight:x='0:1' weight:y='0:1' pos:sticky='nswe'
                \label text=[pages.signin.label.password] pos:grid=0,0 pos:sticky='w' font='"Nova Square" 15'
                \entry show='*' text={{password}} font='"Nova Square" 18' pos:grid=1,0 width=30 pos:sticky='e'
        \frame pos:grid=0,1 pos:sticky='nsew' weight:x='1: 10'
            \ctk.button command={gt_signup} text=[pages.signin.gt_signup] pos:grid=0,0 pos:sticky='sw'
            \ctk.button command={signin} text=[pages.signin.submit] pos:grid=2,0 pos:sticky='se'
    """

    def __init__(self, redirect):
        self.redirect = redirect
        super().__init__()

    username = ""
    password = ""

    def signin(self):
        name = self["username"]
        password = self["password"]
        try:
            user = User.login(name, password)
        except User.DoesNotExist:
            Notification(
                "Todos",
                "Wrong login: please verify credentials and re-enter",
                bootstyle="danger",
                source=None,
                duration=10000,
            ).show()
        else:
            Notification(
                "Todos",
                "Signin successful",
                bootstyle="info",
                source="signin-page",
                duration=5000,
            ).show()
            taktk.application.view.url(self.redirect)

    def gt_signup(self):
        taktk.application.view.url("sign#signup")


def signin(store, /, redirect="todos"):
    return Signin(redirect=redirect)


class Signup(Component):
    r"""
    \frame:form weight:x='0: 1' weight:y='0: 1' padding=20
        \frame:form pos:grid=0,0 weight:x='0:1'
            \frame pos:grid=0,0 padding=20 weight:x='0:1' weight:y='0:1' pos:sticky='nswe'
                \label text=[pages.signin.label.name] pos:grid=0,0 pos:sticky='w' font='"Nova Square" 15'
                \entry text={{username}} font='"Nova Square" 18' pos:grid=1,0 width=30 pos:sticky='e'
            \frame pos:grid=0,1 padding=20 weight:x='0:1' weight:y='0:1' pos:sticky='nswe'
                \label text=[pages.signin.label.password] pos:grid=0,0 pos:sticky='w' font='"Nova Square" 15'
                \entry show='*' text={{password}} font='"Nova Square" 18' pos:grid=1,0 width=30 pos:sticky='e'
                \entry show='*' text={{password2}} font='"Nova Square" 18' pos:grid=1,1 width=30 pos:sticky='e'
        \frame:buttons pos:grid=0,1 pos:sticky='nsew' weight:x='1: 10'
            \ctk.button command={gt_signin} text=[pages.signin.gt_signin] pos:grid=0,0 pos:sticky='sw'
            \ctk.button command={signup} text=[pages.signin.submit] pos:grid=2,0 pos:sticky='se'
    """

    def __init__(self, redirect):
        self.redirect = redirect
        super().__init__()

    username = ""
    password = ""
    password2 = ""

    def signup(self):
        name = self["username"]
        password = self["password"]
        if self["password"] != self["password2"]:
            Notification(
                "Todos",
                "Unmatching password",
                duration=5000,
                bootstyle="danger",
            ).show()
            return
        try:
            user = User.signup(name, password)
        except User.DoesExist:
            Notification(
                "Todos",
                "User already exists",
                bootstyle="danger",
                source=None,
                duration=10000,
            ).show()
        else:
            Notification(
                "Todos",
                "Signup successful",
                bootstyle="info",
                source="signin-page",
                duration=5000,
            ).show()
            taktk.application.view.url(self.redirect)

    def gt_signin(self):
        taktk.application.view.url("sign#signin")


def signup(store, /, redirect="todos"):
    return Signup(redirect=redirect)
