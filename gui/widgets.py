import os
from tkinter import Frame, Canvas, Button, PhotoImage, Label, OptionMenu, StringVar, Entry
from tkinter.constants import LEFT, TOP, BOTH

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from engine.time_spaced_signals import signal_funcs


class Scroller(Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.draw_scroller()
        self.pack()

    def draw_scroller(self):
        half_height = int(self['height'])//2
        self.create_line(
            (0, half_height),
            (self['width'], half_height),
            fill='black'
        )
        radius = 5
        self.create_oval((0, half_height-radius), (2*radius, half_height+radius), fill='black')


class PlayWidget(Frame):
    images = {}

    def __init__(self):
        super().__init__()

        self.upload_static()
        self.play_button = Button(self, image=self.images['play'])
        self.play_button.pack(side=LEFT, padx=5)

        self.pause_button = Button(self, image=self.images['pause'])
        self.pause_button.pack(side=LEFT, padx=5)

        self.stop_button = Button(self, image=self.images['stop'])
        self.stop_button.pack(side=LEFT, padx=5)

        self.backward_button = Button(self, image=self.images['backward'])
        self.backward_button.pack(side=LEFT, padx=5)

        self.forward_button = Button(self, image=self.images['forward'])
        self.forward_button.pack(side=LEFT, padx=5)

        self.scroll_canvas = Scroller(self, height=30)
        self.scroll_canvas.pack(side=LEFT, padx=5)
        self.timeline_label = Label(self, text='00:00')
        self.timeline_label.pack(side=LEFT, padx=5)

        self.pack()

    def upload_static(self):
        folder = 'static'
        for file in os.listdir(folder):
            filename = file.split('.')[0]
            self.images[filename] = PhotoImage(file=f'{folder}/{file}')


class PlotWidget(Frame):
    def __init__(self):
        super().__init__()

        self.fig = Figure()
        t = np.arange(0, 3, .01)
        self.ax = self.fig.add_subplot()
        self.ax.plot(t, 2 * np.sin(2 * np.pi * t))
        self.ax.grid()
        self.ax.set_xlabel("time [s]")
        self.ax.set_ylabel("f(t)")

        self.screen = FigureCanvasTkAgg(self.fig, master=self)  # A tk.DrawingArea.
        self.screen.draw()

        self.screen.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)

        self.pack()

    def draw_screen(self, time_vec: np.array, vals:np.array):
        self.fig.delaxes(self.ax)
        self.ax = self.fig.add_subplot()
        self.ax.plot(time_vec, vals)
        self.ax.grid()
        self.screen.draw()

        self.screen.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)


class Channel(Frame):
    def __init__(self, channel_num: int):
        super().__init__()

        self.channel_label = Label(self, text=f'Channel {channel_num}')
        self.channel_label.pack(side=LEFT)

        self.selected = StringVar(self)
        self.selected.set('Select signal type')
        self.options = OptionMenu(self, self.selected, *signal_funcs)
        self.options.pack(side=LEFT)

        self.freq_label = Label(self, text='Frequency')
        self.freq_label.pack(side=LEFT)
        self.freq_param = Entry(self, width=8, state='disabled')
        self.freq_param.pack(side=LEFT)

        self.add_label = Label(self, text='Additional')
        self.add_label.pack(side=LEFT)
        self.add_param = Entry(self, width=3, state='disabled')
        self.add_param.pack(side=LEFT)

        self.confirm_button = Button(self, text='Add to main stream')
        self.confirm_button.pack(side=LEFT)

        self.pack()


class ControlPanel(Frame):
    def __init__(self):
        super().__init__()

        self.channels = [Channel(i) for i in range(1, 9)]

        self.pack()


if __name__ == '__main__':
    from tkinter import Tk

    root = Tk()
    plot_widget = PlotWidget()
    play_widget = PlayWidget()
    control_widget = ControlPanel()
    root.mainloop()