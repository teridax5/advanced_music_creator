import io
import subprocess
import wave
from collections.abc import Callable
from threading import Thread, Event
from typing import Dict, List

from pydub.playback import play

from engine.time_spaced_signals import *


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
        self.signal_shape = np.array([])
        self.thread = None

    def __repr__(self):
        sound_info = f"{self.path if self.path else 'gen'} "
        for key, value in self.sound_info.items():
            sound_info += f" {key}:{value} "
        sound_info += f"duration:{self.track_length}"
        return sound_info

    def __eq__(self, other):
        return self.sound_info == other.sound_info

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
        self, start_frame: int | None = None, end_frame: int | None = None
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

    def generate_time_spaced_signal(
        self,
        source: Callable,
        frame_rate: int,
        source_kwargs: dict,
        duration: int,
        delay,
    ):
        """
        Generate signal based on input and writes np.array into signal_shape
        field

        :param delay: Delay for the signal
        :param source: A callable, which returns time-spaced signal
        :param frame_rate: Frame rate for signal
        :param source_kwargs: Keyword args for source
        :param duration: Duration in seconds for audio signal
        :return:
        """
        time_vector = np.array([i for i in range(frame_rate * duration)])
        window = 0.5  # * np.hamming(len(time_vector))

        source_kwargs["time_vector"] = time_vector
        source_kwargs["frate"] = frame_rate
        signal = window * source(**source_kwargs)
        if delay:
            signal = np.append(np.zeros(delay * frame_rate), signal)
        self.signal_shape = signal

    @staticmethod
    def encode_time_spaced_signal(
        signal: np.array,
        width: int,
    ):
        """
        Encode time-spaced signal in np.array

        :param signal: Input signal
        :param width: Byte height of the signal
        :return: Bytes of the result
        """
        amplitude = 2 ** (8 * width - 1)

        encoded_signal = []
        for frame in amplitude * signal:
            high, low = divmod(int(frame), 0x100)
            encoded_signal += [low, high]
        return encoded_signal

    def write_metadata(
        self,
        encoded_signal: bytes,
        channels: int,
        width: int,
        frame_rate: int,
        duration: int,
    ):
        """
        Writes metadata of result audio signal into fields

        :param duration: Duration in secs for sample
        :param encoded_signal: Bytes of the encoded signal
        :param channels: Number of channels (mono, stereo etc...)
        :param width: Byte height of the sample
        :param frame_rate: Sample's number of frames
        :return:
        """
        self.content = bytes(encoded_signal)
        self.sound_info = {
            "nchannels": channels,
            "sampwidth": width,
            "framerate": frame_rate,
        }
        self.track_length = duration

    def create_new_sound(
        self,
        source: Callable,
        frame_rate: int,
        width: int,
        source_kwargs: dict,
        save_name: str | None = None,
        duration: int = 1,
        time_shift: int = 0,
    ):
        """
        Converts signal points from source into audio with parameters given
        and saves result

        :param time_shift: Time delay for the sound
        :param source: Callable object to get sound shape data
        :param frame_rate: Frame rate of the sound
        :param width: Number of octets to be encoded
        :param source_kwargs: Additional args for specific signal (see for
        concrete signal to get its kwargs)
        :param save_name: A path to save the file (optional)
        :param duration: Duration of sample in seconds
        :return:
        """
        self.generate_time_spaced_signal(
            source=source,
            frame_rate=frame_rate,
            source_kwargs=source_kwargs,
            duration=duration,
            delay=time_shift,
        )
        signal = self.signal_shape
        encoded_signal = self.encode_time_spaced_signal(
            signal=signal,
            width=width,
        )
        self.write_metadata(
            encoded_signal=encoded_signal,
            channels=1,
            width=width,
            frame_rate=frame_rate,
            duration=duration + time_shift,
        )

        if save_name:
            self.save(save_name)


class AudioDriver:
    time_spaced_signals = signals

    def __init__(self):
        self.threads: List[Thread] = []
        self.audio_files: Dict[str, AudioFile] = {}
        self.stopped_at = None

    def add_to_threads(self, audio: str):
        """
        Adds audio file from audio files dict by key to threads list
        :param audio: The key of a certain audio sample
        :return:
        """
        audio_file = self.audio_files.get(audio, None)
        if not audio_file:
            return
        audio_file.get_sound_info()
        audio_file.get_music_thread(
            self.stopped_at if self.stopped_at else 0,
            audio_file.track_length
        )
        print(self.stopped_at)
        self.threads.append(self.audio_files[audio].thread)

    def create_new_sample(
        self,
        signal: Callable,
        freq: int,
        frame_rate: int,
        width: int,
        duration: int,
        channel_name: str,
        save_name: str | None = None,
        time_shift: int = 0,
    ):
        """
        Creates new audio file by given parameters and puts it into audio
        files dict

        :param channel_name: Name of the channel
        :param time_shift: Time after sample starts
        :param signal: A function to generate certain time-spaced signal
        :param freq: A frequency of the signal
        :param frame_rate: A frame rate for the sample
        :param width: A byte height of the signal
        :param duration: A duration of the sample
        :param save_name: At which name the sample should be saved
        :return: Result's signal name
        """
        if save_name:
            save_name = save_name + ".wav"
        new_sample = AudioFile()
        new_sample.create_new_sound(
            source=signal,
            source_kwargs={"freq": freq},
            frame_rate=frame_rate,
            width=width,
            save_name=save_name,
            duration=duration,
            time_shift=time_shift,
        )
        audio_name = channel_name
        self.audio_files[audio_name] = new_sample
        return audio_name

    def adjust_two_signals(self, key1: str, key2: str):
        """
        Adjust duration between two signals

        :param key1: The first sample by key in audio files
        :param key2: The second sample by key in audio files
        :return: Both signals, their AudioFile objects and sizes
        """
        audio1 = self.audio_files.get(key1, None)
        audio2 = self.audio_files.get(key2, None)
        if not audio1 == audio2:
            raise Exception("Samples have different parameters!")
        signal1 = audio1.signal_shape
        signal2 = audio2.signal_shape

        size1 = len(signal1)
        size2 = len(signal2)
        if size1 != size2:
            if size1 > size2:
                signal2 = np.append(signal2, np.zeros(size1 - size2))
            else:
                signal1 = np.append(signal1, np.zeros(size2 - size1))
        return signal1, signal2, audio1, audio2, size1, size2

    def join_by_sum(self, key1: str, key2: str):
        """
        Join two signals taken by keys and mixes them into one by the rule of
        parallel signals' sum

        :param key1: The first sample by key in audio files
        :param key2: The second sample by key in audio files
        :return:
        """
        signal1, signal2, audio1, audio2, _, _ = self.adjust_two_signals(
            key1, key2
        )

        joined = signal1 + signal2
        joined = 0.5 / max(joined) * joined

        joined_audio = AudioFile()
        joined_audio.signal_shape = joined
        joined_encoded = joined_audio.encode_time_spaced_signal(
            signal=joined, width=2
        )
        joined_audio.content = bytes(joined_encoded)
        joined_audio.sound_info = audio1.sound_info.copy()
        joined_audio.track_length = max(
            audio1.track_length, audio2.track_length
        )
        self.audio_files["joined_by_sum"] = joined_audio

    def join_by_max(self, key1: str, key2: str):
        """
        Join two signals taken by keys and mixes them into one by the rule of
        maximum in each frame

        :param key1: The first sample by key in audio files
        :param key2: The second sample by key in audio files
        :return:
        """
        signal1, signal2, audio1, audio2, size1, size2 = (
            self.adjust_two_signals(key1, key2)
        )

        result = []
        for idx in range(max(size1, size2)):
            result.append(max(signal1[idx], signal2[idx]))
        result = np.array(result)

        joined_audio = AudioFile()
        joined_audio.signal_shape = result
        joined_encoded = joined_audio.encode_time_spaced_signal(
            signal=result, width=2
        )
        joined_audio.content = bytes(joined_encoded)
        joined_audio.sound_info = audio1.sound_info.copy()
        joined_audio.track_length = max(
            audio1.track_length, audio2.track_length
        )
        self.audio_files["joined_by_max"] = joined_audio

    def make_stereo_sound(
        self, key1: str, key2: str | None = None, right_to_left: bool = True
    ):
        """
        Join two samples into one two channeled (stereo); by default
        the first audio goes to right channel

        :param key1: The first sample by key in audio files
        :param key2: The second sample by key in audio files
        :param right_to_left: Order of channels for input samples
        :return:
        """
        audio1 = self.audio_files.get(key1, None)
        audio2 = self.audio_files.get(key2, None)
        if not audio1:
            return
        if not audio2:
            audio2 = AudioFile()
            audio2.content = bytes([0] * len(audio1.content))
            audio2.sound_info = audio1.sound_info.copy()
            audio2.track_length = audio1.track_length

        result_bytes = bytearray()
        if right_to_left:
            bytes1 = audio2.content
            bytes2 = audio1.content
        else:
            bytes1 = audio1.content
            bytes2 = audio2.content
        for i in range(0, min(len(bytes1), len(bytes2)), 2):
            result_bytes.extend(bytes1[i : i + 2] + bytes2[i : i + 2])
        result_bytes = bytes(result_bytes)

        new_file = AudioFile()
        new_file.content = result_bytes
        new_file.sound_info = audio1.sound_info.copy()
        new_file.track_length = audio1.track_length
        new_file.sound_info["nchannels"] = 2
        self.audio_files["stereo"] = new_file

    def play_threads(self):
        if not self.threads:
            return

        for thread in self.threads:
            thread.start()


if __name__ == "__main__":
    # af = AudioFile("rev_step100Hz.wav")
    # af.get_sound_info()
    # af.get_music_thread(0, 10)
    # af1 = AudioFile("")
    # af.thread.start()
    # af.thread.join()
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
    driver = AudioDriver()
    driver.create_new_sample(
        signal=driver.time_spaced_signals[0],
        freq=600,
        frame_rate=96000,
        width=2,
        duration=6,
        channel_name="Channel 1",
    )
    driver.create_new_sample(
        signal=driver.time_spaced_signals[0],
        freq=300,
        frame_rate=96000,
        width=2,
        duration=4,
        time_shift=2,
        channel_name="Channel 2",
    )
    driver.create_new_sample(
        signal=driver.time_spaced_signals[0],
        freq=500,
        frame_rate=96000,
        width=2,
        duration=2,
        channel_name="Channel 3",
    )
    keys = tuple(driver.audio_files.keys())
    print(keys)
    sample_names = keys[:2]
    driver.join_by_sum(*sample_names)
    # driver.make_stereo_sound(*sample_names)
    # for key in driver.audio_files.keys():
    #     driver.add_to_threads(key)
    driver.add_to_threads("joined_by_sum")
    driver.play_threads()
