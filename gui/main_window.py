from tkinter import Tk


class MainWindow(Tk):
    width = 700
    height = 700

    def __init__(self):
        super().__init__()

        self.init_window()

        self.mainloop()

    def init_window(self):
        x_coord, y_coord = (
            (self.winfo_screenwidth() - self.width) // 2,
            (self.winfo_screenheight() - self.height) // 2,
        )
        self.geometry(f"{self.width}x{self.height}+{x_coord}+{y_coord}")
        self.title("MP3 Creator")


if __name__ == "__main__":
    MainWindow()
