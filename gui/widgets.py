import os
from tkinter import (
    Button,
    Canvas,
    Entry,
    Frame,
    Label,
    OptionMenu,
    PhotoImage,
    StringVar,
)
from tkinter.constants import BOTH, END, LEFT, TOP

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import engine.time_spaced_signals as signal_lib


def time_format(num: int) -> str:
    """
    Takes duration of the sample and return its duration in minutes/seconds

    :param num: duration of sample
    :return: String format of track duration
    """
    minutes = int(num // 60)
    seconds = int(num % 60)
    min_str = str(minutes)
    sec_str = str(seconds)
    if minutes < 10:
        min_str = f"0{minutes}"
    if seconds < 10:
        sec_str = f"0{seconds}"
    return f"{min_str}:{sec_str}"


class Scroller(Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.draw_scroller()
        self.pack()

    def draw_scroller(self):
        half_height = int(self["height"]) // 2
        self.create_line(
            (5, half_height), (self["width"], half_height), fill="black"
        )
        radius = 5
        self.create_oval(
            (0, half_height - radius),
            (2 * radius, half_height + radius),
            fill="black",
            tags="cursor",
        )


class PlayWidget(Frame):
    images = {}

    def __init__(self, end_time: int = 0):
        super().__init__()

        self.upload_static()
        self.timer = 0
        self.end_time = end_time
        self.paused = False
        self.stopped = False

        self.play_button = Button(self, image=self.images["play"])
        self.play_button.pack(side=LEFT, padx=5)

        self.pause_button = Button(self, image=self.images["pause"])
        self.pause_button.pack(side=LEFT, padx=5)

        self.stop_button = Button(self, image=self.images["stop"])
        self.stop_button.pack(side=LEFT, padx=5)

        self.backward_button = Button(self, image=self.images["backward"])
        self.backward_button.pack(side=LEFT, padx=5)

        self.forward_button = Button(self, image=self.images["forward"])
        self.forward_button.pack(side=LEFT, padx=5)

        self.scroll_canvas = Scroller(self, height=30)
        self.scroll_canvas.pack(side=LEFT, padx=5)

        self.timeline_label = Label(self, text="00:00")
        self.timeline_label.pack(side=LEFT, padx=5)

        self.endtime_label = Label(self, text=f"/  {time_format(end_time)}")
        self.endtime_label.pack(side=LEFT)

        self.join_channels_by_max = Button(self, text="Join by max")
        self.join_channels_by_max.pack(side=LEFT, padx=5)

        self.join_channels_by_max = Button(self, text="Join by sum")
        self.join_channels_by_max.pack(side=LEFT, padx=5)

        self.join_channels_by_max = Button(self, text="Join channels")
        self.join_channels_by_max.pack(side=LEFT, padx=5)

        self.selected_sample = Label(self, text="Select sample")
        self.selected_sample.pack(side=LEFT, padx=5)
        self.sample_var = StringVar(self)
        self.sample_var.set("No samples")
        self.empty_option = "No samples"
        self.samples = []
        self.sample_options = OptionMenu(
            self, self.sample_var, *[self.empty_option]
        )
        self.sample_options.pack(side=LEFT, padx=5)
        self.samples.append("Sample1")
        self.refresh_samples()
        self.samples = []
        self.refresh_samples()

        self.pack()

    def refresh_samples(self):
        # Reset var and delete all old options
        self.sample_var.set(
            self.samples[-1] if self.samples else self.empty_option
        )
        self.sample_options["menu"].delete(0, "end")

        def set_new_value(val):
            def set_val():
                self.sample_var.set(val)

            return set_val

        # Insert list of new options (tk._setit hooks them up to var)
        if self.samples:
            options = self.samples
        else:
            options = [self.empty_option]
        for choice in options:
            self.sample_options["menu"].add_command(
                label=choice, command=set_new_value(choice)
            )

    def move_time_cursor(self, event=None):
        if (self.timer == self.end_time) or self.stopped:
            self.scroll_canvas.delete('cursor')
            self.scroll_canvas.draw_scroller()
            self.timeline_label["text"] = time_format(0)
            if self.stopped:
                self.stopped = False
            return
        if not event:
            self.endtime_label["text"] = time_format(self.end_time)
        if self.paused:
            self.paused = False
            return
        self.scroll_canvas.move(
            "cursor",
            (int(self.scroll_canvas["width"]) - 10) / self.end_time,
            0,
        )
        self.timer += 1
        self.timeline_label["text"] = time_format(self.timer)
        self.after(1000, self.move_time_cursor)

    def upload_static(self):
        folder = "static"
        for file in os.listdir(folder):
            filename = file.split(".")[0]
            self.images[filename] = PhotoImage(file=f"{folder}/{file}")


class PlotWidget(Frame):
    def __init__(self):
        super().__init__()

        self.fig = Figure(figsize=(13, 4))
        self.ax = self.fig.add_subplot()
        self.ax.plot()
        self.ax.grid()
        self.ax.set_xlabel("time [s]")
        self.ax.set_ylabel("f(t)")
        self.plots = {}

        self.screen = FigureCanvasTkAgg(
            self.fig, master=self
        )  # A tk.DrawingArea.
        self.screen.draw()

        self.screen.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)

        self.pack()

    def draw_screen(self, time_vec: np.array, vals: np.array, lbl: str):
        self.fig.delaxes(self.ax)
        self.ax = self.fig.add_subplot()
        self.plots.update({lbl: self.ax.plot(time_vec, vals, label=lbl)[0]})
        self.ax.grid()
        self.ax.legend(loc="best")
        self.screen.draw()

        self.screen.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)

    def add_graph(self, time_vec: np.array, vals: np.array, lbl: str):
        self.plots.update({lbl: self.ax.plot(time_vec, vals, label=lbl)[0]})
        self.ax.legend(loc="best")
        self.screen.draw()

    def remove_graph(self, channel_name):
        plot = self.plots.get(channel_name, None)
        if not plot:
            return
        plot.remove()
        del self.plots[channel_name]
        if not self.plots:
            self.ax.get_legend().set_visible(False)
        self.screen.draw()


class Channel(Frame):
    def __init__(self, channel_num: int):
        super().__init__()

        self.name = f"Channel {channel_num}"

        self.settings_frame = Frame(self)

        self.channel_label = Label(self.settings_frame, text=self.name)
        self.channel_label.pack(side=LEFT)

        self.selected = StringVar(self.settings_frame)
        self.default_option = "Select signal type"
        self.selected.set(self.default_option)
        self.selected.trace("w", self.update_option)
        self.options = OptionMenu(
            self.settings_frame,
            self.selected,
            *(self.default_option,) + signal_lib.signal_funcs,
        )
        self.options.config(width=30)
        self.options.pack(side=LEFT)

        self.freq_label = Label(self.settings_frame, text="Frequency")
        self.freq_label.pack(side=LEFT)
        self.freq_param = Entry(self.settings_frame, width=8, state="disabled")
        self.freq_param.pack(side=LEFT)

        self.width_param = StringVar(self.settings_frame)
        self.width_param.trace("w", self.choose_width)
        self.width_param.set("2")
        self.width_label = Label(self.settings_frame, text="Sample width")
        self.width_label.pack(side=LEFT)
        self.width_opts = OptionMenu(
            self.settings_frame,
            self.width_param,
            *[str(i) for i in range(1, 5)],
        )
        self.width_opts.pack(side=LEFT)

        self.frate_param = StringVar(self.settings_frame)
        frame_rates = ["44100", "48000", "96000", "144000", "192000"]
        self.frate_param.trace("w", self.choose_frate)
        self.frate_param.set(frame_rates[0])
        self.frate_label = Label(self.settings_frame, text="Frame rate")
        self.frate_label.pack(side=LEFT)
        self.frate_options = OptionMenu(
            self.settings_frame, self.frate_param, *frame_rates
        )
        self.frate_options.pack(side=LEFT)

        self.add_label = Label(self.settings_frame, text="Additional")
        self.add_label.pack(side=LEFT)
        self.add_param = Entry(self.settings_frame, width=3, state="disabled")
        self.add_param.pack(side=LEFT)

        self.duration_label = Label(self.settings_frame, text="Duration(secs)")
        self.duration_label.pack(side=LEFT)
        self.duration_param = Entry(
            self.settings_frame, width=3, state="disabled"
        )
        self.duration_param.pack(side=LEFT)

        self.shift_label = Label(self.settings_frame, text="Time shift(secs)")
        self.shift_label.pack(side=LEFT)
        self.shift_param = Entry(
            self.settings_frame, width=3, state="disabled"
        )
        self.shift_param.pack(side=LEFT)

        self.confirm_button = Button(
            self.settings_frame,
            text="Add to audio files",
            state="disabled",
            command=self.button_action,
        )
        self.confirm_button.pack(side=LEFT)

        self.remove_button = Button(
            self.settings_frame,
            text="Remove from audio files",
            state="disabled",
            command=self.remove_action,
        )
        self.remove_button.pack(side=LEFT)

        self.state_label = Label(self.settings_frame, text="")
        self.state_label.pack(side=LEFT)

        self.settings_frame.pack()

        self.pack()

    def update_option(self, *args):
        widgets_to_update = [
            self.freq_param,
            self.add_param,
            self.confirm_button,
            self.remove_button,
            self.duration_param,
            self.shift_param,
        ]
        if self.selected.get() == self.default_option:
            for widget in widgets_to_update:
                if isinstance(widget, Entry):
                    widget.delete(0, END)
                widget["state"] = "disabled"
            self.state_label["text"] = ""
        else:
            for widget in widgets_to_update:
                widget["state"] = "normal"

    def choose_width(self, *args):
        if self.selected.get() != self.default_option:
            self.data.update({"width": int(self.width_param.get())})
        else:
            self.width_param.set("2")

    def choose_frate(self, *args):
        if self.selected.get() != self.default_option:
            self.data.update({"frame_rate": int(self.frate_param.get())})
        else:
            self.frate_param.set("44100")

    @property
    def data(self):
        return dict(
            signal=getattr(signal_lib, self.selected.get()),
            freq=int(self.freq_param.get()),
            frame_rate=int(self.frate_param.get()),
            width=int(self.width_param.get()),
            duration=int(self.duration_param.get()),
            time_shift=int(self.shift_param.get()),
        )

    def button_action(self):
        try:
            self.data
        except:
            self.state_label["text"] = "Error"
        else:
            self.state_label["text"] = "Added"

    def remove_action(self):
        self.state_label["text"] = "Removed"


class ControlPanel(Frame):
    def __init__(self):
        super().__init__()

        self.channels = [Channel(i) for i in range(1, 9)]
        self.channels_dict = {
            channel.name: channel for channel in self.channels
        }

        self.pack()


if __name__ == "__main__":
    from tkinter import Tk

    root = Tk()
    plot_widget = PlotWidget()
    play_widget = PlayWidget()
    control_widget = ControlPanel()
    root.mainloop()
