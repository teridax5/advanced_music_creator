import os
from tkinter import Tk

import psutil

from engine import AudioDriver
from gui.widgets import ControlPanel, PlayWidget, PlotWidget


class MainWindow(Tk):
    width = 700
    height = 700

    def __init__(self):
        super().__init__()

        self.init_window()
        self.audio_driver = AudioDriver()
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

        self.player.play_button.bind(
            "<Button-1>",
            self.add_to_thread_and_play
        )
        self.player.stop_button.bind(
            "<Button-1>",
            self.stop_playing
        )
        self.player.pause_button.bind(
            "<Button-1>",
            self.pause_playing
        )
        self.process = psutil.Process(os.getpid())

        self.mainloop()

    def init_window(self):
        self.title("MP3 Creator")

    def catch_button_press(self, channel_name):
        def build_plot(event):
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
            points = audio.signal_shape
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
            self.player.samples.append(channel_name)
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
        if (audio:=self.player.sample_var.get()) != self.player.empty_option:
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


if __name__ == "__main__":
    MainWindow()
