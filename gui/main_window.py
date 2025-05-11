import os
from tkinter import Tk, Toplevel, OptionMenu, StringVar, Button, Entry

import psutil

from engine import AudioDriver
from gui.widgets import ControlPanel, PlayWidget, PlotWidget


class MainWindow(Tk):
    width = 700
    height = 700

    def __init__(self):
        super().__init__()

        self.init_window()
        self.process = psutil.Process(os.getpid())
        self.audio_driver = AudioDriver()
        self.sample_pair = None

        self.plot = PlotWidget()
        self.player = PlayWidget()
        self.control = ControlPanel()

        for channel in self.control.channels:
            channel.confirm_button.bind(
                "<Button-1>", self.catch_button_press(channel.name)
            )
            channel.remove_button.bind(
                "<Button-1>", self.catch_remove(channel.name)
            )

        self.player.play_button.bind("<Button-1>", self.add_to_thread_and_play)
        self.player.stop_button.bind("<Button-1>", self.stop_playing)
        self.player.pause_button.bind("<Button-1>", self.pause_playing)

        self.player.join_channels_by_max.bind("<Button-1>", self.join_by_max)
        self.player.join_channels_by_sum.bind("<Button-1>", self.join_by_sum)
        self.player.join_channels.bind("<Button-1>", self.join_channels)
        self.player.add_filter.bind("<Button-1>", self.add_filter)
        self.player.save_button.bind("<Button-1>", self.save_sample)

        self.mainloop()

    def init_window(self):
        self.title("MP3 Creator")

    def catch_button_press(self, channel_name):
        def build_plot(event):
            if channel_name in self.plot.plots.keys():
                self.plot.remove_graph(channel_name)
            channel = self.control.channels_dict.get(channel_name, None)
            try:
                data = channel.data
                data["channel_name"] = channel_name
            except:
                raise Exception("Invalid data!")
            signal_name = self.audio_driver.create_new_sample(**data)
            audio = self.audio_driver.audio_files.get(signal_name, None)
            if not audio:
                return
            points = audio.signal_shape[:audio.sound_info["framerate"]]
            if self.plot.plots:
                self.plot.add_graph(
                    [i for i in range(len(points))],
                    points,
                    lbl=channel_name,
                )
            else:
                self.plot.draw_screen(
                    [i for i in range(len(points))],
                    points,
                    lbl=channel_name,
                )
            self.player.samples.add(channel_name)
            self.player.refresh_samples()

        return build_plot

    def catch_remove(self, channel_name):
        def remove_plot(event):
            channel = self.control.channels_dict.get(channel_name, None)
            if not channel:
                return
            self.plot.remove_graph(channel_name)
            channel.selected.set(channel.default_option)
            self.player.samples.remove(channel_name)
            self.player.refresh_samples()

        return remove_plot

    def add_to_thread_and_play(self, event):
        if (audio := self.player.sample_var.get()) != self.player.empty_option:
            if not self.audio_driver.stopped_at:
                self.player.timer = 0
                self.audio_driver.stopped_at = None
            self.audio_driver.threads = []
            self.audio_driver.add_to_threads(audio)
            audio_file = self.audio_driver.audio_files.get(audio, None)
            if not audio_file:
                return
            self.player.end_time = audio_file.track_length
            self.after(1000, self.player.move_time_cursor)
            self.audio_driver.play_threads()

    def stop_playing(self, event):
        if self.audio_driver.threads:
            for proc in self.process.children(recursive=True):
                proc.kill()
            self.audio_driver.stopped_at = None
            self.player.stopped = True

    def pause_playing(self, event):
        if self.audio_driver.threads:
            for proc in self.process.children(recursive=True):
                proc.kill()
            self.audio_driver.stopped_at = self.player.timer
            self.player.paused = True

    def call_subwindow(self):
        if not self.player.samples:
            return
        sub = Toplevel(self)

        choice1 = StringVar(sub)
        choice1.set(self.player.empty_option)
        options = self.player.samples
        sample1 = OptionMenu(sub, choice1, *options)
        sample1.pack(side="left")

        choice2 = StringVar(sub)
        choice2.set(self.player.empty_option)
        options = self.player.samples
        sample2 = OptionMenu(sub, choice2, *options)
        sample2.pack(side="left")

        def apply():
            self.sample_pair = (choice1.get(), choice2.get())
            sub.destroy()

        apply_option = Button(sub, text="Apply", command=apply)
        apply_option.pack()

    def call_filter_window(self):
        from engine.filters import filters

        if not self.player.samples:
            return
        sub = Toplevel(self)

        sample_var = StringVar(sub)
        sample_var.set(self.player.empty_option)
        options = self.player.samples
        sample = OptionMenu(sub, sample_var, *options)
        sample.pack(side="left")

        filter_var = StringVar(sub)
        filter_var.set(self.player.empty_option)
        options = filters
        sample2 = OptionMenu(sub, filter_var, *options)
        sample2.pack(side="left")

        param = Entry(sub, width=8)
        param.pack(side="left")

        def apply():
            audio = self.audio_driver.audio_files.get(sample_var.get())
            if not audio:
                return
            audio.add_filter(filter_var.get(), {"param": float(param.get())})
            new_name = f"{filter_var.get()}_{sample_var.get()}"
            self.player.samples.remove(sample_var.get())
            self.player.samples.add(new_name)
            self.player.refresh_samples()
            self.audio_driver.audio_files[new_name] = (
                self.audio_driver.audio_files.pop(sample_var.get())
            )
            sub.destroy()

        apply_option = Button(sub, text="Apply", command=apply)
        apply_option.pack()

    def join_by_max(self, event):
        if not self.sample_pair:
            self.call_subwindow()
            return
        self.audio_driver.join_by_max(*self.sample_pair)
        self.player.samples.add("joined_by_max")
        self.player.refresh_samples()
        self.audio_driver.add_to_threads("joined_by_max")

    def join_by_sum(self, event):
        if not self.sample_pair:
            self.call_subwindow()
            return
        self.audio_driver.join_by_sum(*self.sample_pair)
        self.player.samples.add("joined_by_sum")
        self.player.refresh_samples()
        self.audio_driver.add_to_threads("joined_by_sum")

    def join_channels(self, event):
        if not self.sample_pair:
            self.call_subwindow()
            return
        self.audio_driver.make_stereo_sound(*self.sample_pair)
        self.player.samples.add("stereo")
        self.player.refresh_samples()
        self.audio_driver.add_to_threads("stereo")

    def add_filter(self, event):
        self.call_filter_window()

    def save_sample(self, event):
        sample_name = self.player.sample_var.get()
        audio = self.audio_driver.audio_files.get(sample_name)
        audio.save(sample_name)


if __name__ == "__main__":
    MainWindow()
