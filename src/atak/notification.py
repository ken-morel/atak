import time
from threading import Lock, Thread

import yaml
from PIL import ImageTk
from pyoload import *
from ttkbootstrap import *
from ttkbootstrap.icons import *
from ttkbootstrap.utility import *

from . import Nil
from .media import get_image


class Notification:
    MARGIN = 10
    _STACK = []
    WIDTH = 350
    IMAGE_WIDTH = 100
    icon = None
    rearange_lock = Lock()

    def __init__(
        self,
        title,
        message,
        duration=None,
        bootstyle="dark",
        alert=False,
        icon=Nil,
        source=None,
    ):
        self.source = source
        self.message = message
        self.title = title
        self.duration = duration
        self.bootstyle = bootstyle

        self.setup_icon(icon)
        self.titlefont = None

    def setup_icon(self, icon=Nil):
        image = None
        if icon is Nil:
            import taktk

            if taktk.get_app() is None:
                return
            image = taktk.get_app().icon.image
        elif isinstance(icon, str):
            image = get_image(icon).image
        if image is not None:
            w, h = image.size
            sc = Notification.IMAGE_WIDTH / w
            self.icon = ImageTk.PhotoImage(
                image.resize((int(w * sc), int(h * sc)))
            )
        else:
            try:
                sc = Notification.IMAGE_WIDTH / icon.width()
                icon.config(
                    width=int(sc * icon.width()),
                    height=int(sc * icon.height()),
                )
                self.icon = icon
            except Exception:
                pass

    def show(self):
        self.root = window = Toplevel(overrideredirect=True, alpha=0.7)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)
        window.attributes("-topmost", 1)

        root = ttk.Frame(window, bootstyle=self.bootstyle)
        root.grid(column=0, row=0, sticky="nsew")

        if self.icon is not None:
            ttk.Label(
                root,
                image=self.icon,
                compound="image",
                bootstyle=f"{self.bootstyle}-inverse",
                anchor=NW,
            ).grid(row=0, column=0, rowspan=2, sticky=NSEW, padx=(5, 0))

        ttk.Label(
            root,
            text=self.title,
            wraplength=scale_size(root, Notification.WIDTH - 100),
            font="{20px arial}",
            bootstyle=f"{self.bootstyle}-inverse",
            anchor=NW,
        ).grid(row=0, column=1, sticky=NSEW, padx=10, pady=(5, 0))

        ttk.Label(
            root,
            text=self.message,
            wraplength=scale_size(root, Notification.WIDTH - 100),
            bootstyle=f"{self.bootstyle}-inverse",
            anchor=NW,
        ).grid(row=1, column=1, sticky=NSEW, padx=10, pady=(0, 5))

        window.bind("<ButtonPress>", self.hide)
        Thread(target=Notification.add, args=(self,)).start()
        window.bell()

        if self.duration is not None:
            window.after(self.duration, self.hide)

    def hide(self, *_):
        """Destroy and close the toast window."""
        Notification.remove(self)

    def _hide(self):
        alpha = float(self.root.attributes("-alpha"))
        if alpha <= 0.1:
            self.root.destroy()
            Notification.position_widgets()
        else:
            self.root.attributes("-alpha", alpha - 0.1)
            self.root.after(25, self._hide)

    @classmethod
    def add(cls, notification):
        marg = Notification.MARGIN
        width = Notification.WIDTH
        notification.root.update_idletasks()

        height = notification.root.winfo_height()
        screen_height = notification.root.winfo_screenheight()
        for x in range(len(cls._STACK)):
            if (
                cls._STACK[x].source == notification.source
                and notification.source is not None
            ):
                px, py = (
                    cls._STACK[x].root.winfo_rootx(),
                    cls._STACK[x].root.winfo_rooty(),
                )
                cls.remove(cls._STACK[x])
                cls._STACK.insert(x, notification)
                notification.root.geometry(f"{width}x{height}{px:+}{py:+}")
                cls.position_widgets()
                break
        else:
            while True:
                taken = 0
                for notif in Notification._STACK:
                    taken += marg + notif.root.winfo_height()

                if screen_height - (taken + marg) < height:
                    Notification.remove_earliset()
                    continue
                else:
                    break
            cls._STACK.append(notification)
            notification.root.geometry(
                f"{width}x{height}-{marg}-{taken + marg}"
            )

    @classmethod
    def remove_earliset(cls):
        cls.remove(cls._STACK[0])

    @classmethod
    def remove(cls, notification):
        notification._hide()
        if notification in cls._STACK:
            cls._STACK.pop(cls._STACK.index(notification))

    @classmethod
    def position_widgets(cls):
        with cls.rearange_lock:
            marg = cls.MARGIN

            for idx, notification in enumerate(cls._STACK):
                taken = 0
                height = notification.root.winfo_height()
                for notif in cls._STACK[:idx]:
                    taken += marg + notif.root.winfo_height()

                pos2 = taken + marg
                swidth = notification.root.winfo_screenheight()
                while (swidth - notification.root.winfo_y() - height) > pos2:
                    for notif in cls._STACK[idx:]:
                        notif.root.geometry(
                            f"-{marg}+{notif.root.winfo_y() + 10}",
                        )
                        notif.root.update_idletasks()
                    # time.sleep(0.005)
                notification.root.geometry(f"-{marg}-{pos2}")
                notification.root.update_idletasks()
