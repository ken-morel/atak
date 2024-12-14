import tkinter as tk
from tkinter import ttk

import vlc


class VideoPlayer:
    def __init__(self, root, video_path):
        self.root = root
        self.root.title("Tkinter VLC Video Player")

        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.media = self.instance.media_new(video_path)
        self.player.set_media(self.media)

        self.video_panel = ttk.Frame(self.root)
        self.canvas = tk.Canvas(self.video_panel, background="black")
        self.canvas.pack(fill=tk.BOTH, expand=1)
        self.video_panel.pack(fill=tk.BOTH, expand=1)

        self.player.set_hwnd(self.canvas.winfo_id())
        self.player.play()


root = tk.Tk()
VideoPlayer(root, "path_to_your_video.mp4")
root.mainloop()
