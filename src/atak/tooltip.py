import time
from threading import Lock
from threading import Thread

from PIL import ImageTk
from pyoload import *
from ttkbootstrap import *
from ttkbootstrap.icons import *
from ttkbootstrap.tooltip import *
from ttkbootstrap.utility import *


class ToolTip:
    def __init__(
        self,
        widget,
        text,
        bootstyle=None,
        wraplength=None,
        delay=250,  # milliseconds
    ):
        self.widget = widget
        self.text = text
        self.bootstyle = bootstyle
        self.wraplength = wraplength or utility.scale_size(self.widget, 300)
        self.toplevel = None
        self.delay = delay
        self.id = None

        # event binding
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.move_tip)
        self.widget.bind("<ButtonPress>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hide_tip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show_tip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def show_tip(self, *_):
        """Create a show the tooltip window"""
        if self.toplevel:
            return

        self.toplevel = ttk.Toplevel(
            overrideredirect=True, master=self.toplevel
        )
        lbl = ttk.Label(
            master=self.toplevel,
            text=self.text,
            justify=LEFT,
            wraplength=self.wraplength,
            padding=10,
            bootstyle="info",
        )
        lbl.pack(fill=BOTH, expand=YES)
        self.move_tip()
        if self.bootstyle:
            lbl.configure(bootstyle=self.bootstyle)
        else:
            lbl.configure(style="tooltip.TLabel")

    def move_tip(self, *_):
        """Move the tooltip window to the current mouse position within the
        widget.
        """
        if self.toplevel:
            mx = self.widget.winfo_pointerx()
            my = self.widget.winfo_pointery()

            # self.toplevel.update_idletasks()
            w = self.toplevel.winfo_width()
            h = self.toplevel.winfo_height()
            sw = self.toplevel.winfo_screenwidth()
            sh = self.toplevel.winfo_screenheight()

            wx = mx
            wy = my

            if wx + w > sw:
                wx -= w
            if wy + h > sh:
                wy -= h
            self.toplevel.geometry(f"+{wx}+{wy}")

    def hide_tip(self, *_):
        """Destroy the tooltip window."""
        if self.toplevel:
            self.toplevel.destroy()
            self.toplevel = None
