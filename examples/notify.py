from tkinter import Tk

from taktk.component import Component
from taktk.media import Image
from taktk.notification import Notification


class Notifica(Component):
    r"""
    \frame
        \button image=!{julia_image} text='julia' command={notif_julia} pos:grid=0,0
        \button image=!{git_image} text='git' command={notif_git} pos:grid=0,1
        \button image=!{powershell_image} text='powershell' command={notif_powershell} pos:grid=0,2
    """

    code = __doc__

    label_text = "close the window"
    number = 0
    julia_image = Image("../images/julia.png", {"width": 50})

    def notif_julia(self):
        Notification(
            "Julia",
            "Julia notification, click to hide",
            bootstyle="danger",
            icon=self.julia_image.tk,
            duration=5000,
        ).show()

    git_image = Image("../images/git.png", {"width": 50})

    def notif_git(self):
        Notification(
            "Git",
            "Git notification",
            bootstyle="dark",
            icon=self.git_image.tk,
            duration=1000,
        ).show()

    powershell_image = Image("../images/powershell.png", {"width": 50})

    def notif_powershell(self):
        Notification(
            "powershell",
            "powershell notification",
            bootstyle="info",
            duration=3000,
        ).show()


root = Tk()

notifica = Notifica()
notifica.render(root).grid(column=0, row=0)

root.mainloop()
