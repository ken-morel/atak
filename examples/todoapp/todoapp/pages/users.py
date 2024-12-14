import taktk
from taktk.component import Component

from ..admin import User


class Users(Component):
    r"""
    \frame weight:x='0: 10, 1: 2, 2: 10' padding=50
        !enum users:(y, sub_users)
            !enum sub_users:(x, user)
                !if user is not None
                    \frame pos:grid={(x * 2, y)} pos:sticky='nswe' padding=20  weight:x='1: 10' borderwidth=1 relief='solid'
                        \label text={user.name} pos:grid=0,0 pos:sticky='w' font='arial 20'
                        \button bootstyle='info' text=[pages.users.view] pos:grid=2,0 command={lambda u=user.uuid, v=visit: v(u)}
    """

    def init(self):
        users = User.all()
        self["users"] = [
            (users[x], users[x + 1] if x + 1 < len(users) else None)
            for x in range(0, len(users), 2)
        ]

    def visit(self, uuid):
        taktk.application(str(uuid))


def default(store):
    return Users()
