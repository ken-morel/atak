import pystray
from PIL import Image, ImageDraw
import tkinter as tk

def create_image():
    print("Create an image with PIL")
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), (255, 255, 255))
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2 - 10, height // 2 - 10, width // 2 + 10, height // 2 + 10),
        fill=(0, 0, 0))
    return image

def on_clicked(icon, item):
    print("Define what happens when the icon is clicked")
    root = tk.Tk()
    label = tk.Label(root, text="Hello from the system tray!")
    label.pack()
    root.mainloop()

print("Create the icon")
icon = pystray.Icon("test_icon")
icon.icon = create_image()
icon.title = "My App"
icon.menu = pystray.Menu(
    pystray.MenuItem("Open", on_clicked),
    pystray.MenuItem("Quit", lambda icon, item: icon.stop())
)

print("Run the icon")
icon.run()
