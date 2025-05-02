from tkinter import Tk

from gui.widgets import PlotWidget, PlayWidget, ControlPanel


class MainWindow(Tk):
    width = 700
    height = 700

    def __init__(self):
        super().__init__()

        self.init_window()
        self.plot = PlotWidget()
        self.player = PlayWidget()
        self.control = ControlPanel()

        self.mainloop()

    def init_window(self):
        self.title("MP3 Creator")


if __name__ == "__main__":
    MainWindow()
