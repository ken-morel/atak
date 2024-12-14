from tkinter import Tk

from taktk.component import Component
from taktk.dictionary import Dictionary

french = Dictionary.from_directory(locale="French")
english = Dictionary.from_directory(locale="English")
english.install()


class Comp(Component):
    """
    \\frame
        \\frame pos:grid=0,0  padding=5
            \\label text=[label.text] pos:grid=0,0
            \\button text=[button.close] command={close} pos:grid=1,0
        \\frame pos:grid=0,1  padding=5 relief='sunken'
            \\label text={{number}} pos:grid=0,0
            \\ctk.button text=[button.add] command={add} pos:grid=1,0
        \\button pos:grid=0,2 command={toggle} text={btn_text}
    """

    code = __doc__

    number = 0
    btn_text = _.locale

    def close(self):
        root.destroy()
        print("closed")

    def add(self):
        self["number"] += 1
        self.update()

    def toggle(self):
        if _ == english:
            french.install()
        else:
            english.install()
        self["btn_text"] = _.locale


root = Tk()

component = Comp()
component.render(root).grid(column=0, row=0)

root.mainloop()
