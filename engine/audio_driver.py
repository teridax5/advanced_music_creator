import io
import subprocess
import wave
from collections.abc import Callable
from threading import Thread

from pydub.playback import play

from engine.time_spaced_signals import *


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


class AudioFile:
    def __init__(self, path: str | None = None):
        """
        A model for audio file

        :param path: Path (existing or new one) for audio file
        """
        self.path = path
        self.sound_info = {}
        self.content = bytes()
        self.track_length = 0
        self.thread = None

    @property
    def format(self):
        return self.path.split(".")[-1]

    def get_sound_info(self):
        """
        Get info about existing audio file
        """
        if not self.path:
            return
        # load wav-file and its params
        wav_file = wave.open(self.path, "r")
        keys = [
            "nchannels",
            "sampwidth",
            "framerate",
            "nframes",
            "comptype",
            "compname",
        ]
        values = list(wav_file.getparams())
        # creating attribute's dictionary
        self.sound_info = {k: v for k, v in zip(keys, values)}
        # main sound content
        self.content = wav_file.readframes(self.sound_info["nframes"])
        self.track_length = (
            self.sound_info["nframes"] // self.sound_info["framerate"]
        )

    def convert_duration(self, secs: int):
        """
        Converts start and end time points to edge frames

        :param secs: Time in seconds to convert into frame index
        :return: The frame's index
        """
        frame_rate = self.sound_info["framerate"]
        width = self.sound_info["sampwidth"]
        channels = self.sound_info["nchannels"]
        return secs * frame_rate * width * channels

    def play_thread(
        self,
        start_frame: int | None = None,
        end_frame: int | None = None
    ):
        """
        Plays sound file or its fragment

        :param start_frame: Frame from which starts playing audio file
        :param end_frame: Final frame to listen to
        :return:
        """
        from pydub import AudioSegment

        start_idx = start_frame if start_frame else 0
        end_idx = end_frame if end_frame else -1
        memory = io.BytesIO()
        memory.write(self.content[start_idx:end_idx])
        memory.seek(0)
        audio_file = AudioSegment.from_raw(
            memory,
            sample_width=self.sound_info["sampwidth"],
            frame_rate=self.sound_info["framerate"],
            channels=self.sound_info["nchannels"],
        )
        play(audio_file)

    def mp3_to_wav(self):
        subprocess.call(["ffmpeg", "-i", self.path, "audio.wav"])

    def wav_to_mp3(self):
        subprocess.call(f"lame --preset insane {self.path}", shell=True)

    def bytes_to_wav(self, source: str):
        """
        From legacy, maybe no need

        :param source:
        :return:
        """
        src = source
        name = src.split(".")[0]
        self.path = f"converted_{name}.wav"
        subprocess.call(["ffmpeg", "-i", src, self.path])

    def save(self, filename: str):
        """
        Saves audio in wav format from content field using sound_info

        :param filename: Name of file to be saved
        :return:
        """
        wf = wave.open(f"{filename}.wav", "wb")
        wf.setnchannels(self.sound_info["nchannels"])
        wf.setsampwidth(self.sound_info["sampwidth"])
        wf.setframerate(self.sound_info["framerate"])
        wf.writeframes(self.content)
        wf.close()

    def get_music_thread(self, start_time: int, end_time: int):
        """
        Put thread into audio file field with the same name

        :param start_time: Time of the track to start
        :param end_time: Time of the track to end
        :return:
        """
        start_frame = self.convert_duration(start_time)
        end_frame = self.convert_duration(end_time)
        self.thread = Thread(
            target=self.play_thread,
            kwargs={"start_frame": start_frame, "end_frame": end_frame},
            daemon=True,
        )

    def create_new_sound(
        self,
        source: Callable,
        frame_rate: int,
        channels: int,
        width: int,
        source_kwargs: dict,
        save_name: str,
        duration: int = 1
    ):
        """
        Converts signal points from source into audio with parameters given
        and saves result

        :param source: Callable object to get sound shape data
        :param frame_rate: Frame rate of the sound
        :param channels: Number of channels for output audio
        :param width: Number of octets to be encoded
        :param source_kwargs: Additional args for specific signal (see for
        concrete signal to get its kwargs)
        :param save_name: A path to save the file
        :param duration: Duration of sample in seconds
        :return:
        """
        time_vector = np.array([i for i in range(frame_rate * duration)])
        window = 0.5  # * np.hamming(len(time_vector))

        source_kwargs['time_vector'] = time_vector
        source_kwargs['frate'] = frame_rate
        signal = window * source(**source_kwargs)
        amplitude = 2 ** (8 * width - 1)

        encoded_signal = []
        for frame in amplitude * signal:
            high, low = divmod(int(frame), 0x100)
            encoded_signal += [low, high]

        self.content = bytes(encoded_signal)
        self.sound_info = {
            "nchannels": channels,
            "sampwidth": width,
            "framerate": frame_rate,
        }
        self.save(save_name)


if __name__ == "__main__":
    af = AudioFile("rev_step100Hz.wav")
    af.get_sound_info()
    af.get_music_thread(0, 10)
    af.thread.start()
    af.thread.join()
    # new_file = AudioFile()
    # new_file.create_new_sound(
    #     source=generate_step_signal_reversed,
    #     source_kwargs={'freq': 100, 'step_factor':0.3},
    #     frame_rate=96000,
    #     channels=1,
    #     width=2,
    #     save_name='rev_step100Hz',
    #     duration=10,
    # )
