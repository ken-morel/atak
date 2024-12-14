from contextlib import contextmanager
from tkinter import *
from tkinter.ttk import *

import win32con
import win32gui
from PIL import Image, ImageFilter, ImageGrab, ImageTk
from ttkbootstrap import Window


def capture_screen_excluding_window(window):
    """Capture the entire screen, excluding the given window"""
    hwnd = window.winfo_id()
    x0, y0, x1, y1 = (
        window.winfo_rootx(),
        window.winfo_rooty(),
        window.winfo_rootx() + window.winfo_width(),
        window.winfo_rooty() + window.winfo_height(),
    )
    screen_width, screen_height = (
        window.winfo_screenwidth(),
        window.winfo_screenheight(),
    )
    with transparent(window):
        img = ImageGrab.grab(bbox=(x0, y0, x1, y1))
    img_blurred = img.filter(ImageFilter.GaussianBlur(radius=10))
    img_tk = ImageTk.PhotoImage(img_blurred)
    return img_tk


@contextmanager
def transparent(win, alpha=0.3):
    win.attributes("-alpha", alpha)
    yield
    win.attributes("-alpha", 1)


root = Window(themename="superhero")
root.attributes("-transparentcolor", "#555")
root.geometry("500x300")

root.style.configure(
    "Transparent.TFrame",
    bg="#555",
)
frm = Frame(root, style="Transparent.TFrame", bootstyle=None)
label = Label(frm)
label.pack(fill="both", expand=True)
frm.pack(fill="both", expand=True)


def capture_and_display():
    img_tk = capture_screen_excluding_window(root)
    label.config(image=img_tk)
    label.image = img_tk  # keep a reference to the image


# Create a button to capture and display the screen
btn = Button(root, text="Capture", command=capture_and_display)
btn.pack()


root.mainloop()
