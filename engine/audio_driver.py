import numpy as np
from matplotlib import pyplot as plt

from pydub import AudioSegment
from pydub.playback import play

from tkinter import *
import os
from threading import Thread
import subprocess
import re
import wave


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
        min_str = f'0{minutes}'
    if seconds < 10:
        sec_str = f'0{seconds}'
    return f'{min_str}:{sec_str}'


class AudioFile:
    def __init__(self, path: str):
        self.path = path
        self.sound_info = None
        self.content = bytes()
        self.track_length = 0

    def info(self):
        # load wav-file and its params
        wav_file = wave.open(self.path, 'r')
        keys = ['nchannels', 'sampwidth', 'framerate',
                'nframes', 'comptype', 'compname']
        values = list(wav_file.getparams())
        # creating attribute's dictionary
        self.sound_info = {k: v for k,v in (keys, values)}
        # main sound content
        print(self.sound_info)
        self.content = wav_file.readframes(self.sound_info['nframes'])
        self.track_length = self.sound_info['nframes'] \
                            // self.sound_info['framerate']

    def play_thread(self):
        # import required modules
        from pydub import AudioSegment


        # for playing wav file
        audio_file = AudioSegment.from_wav(self.path)
        play(audio_file)

    def mp3_to_wav(self):
        AudioSegment.from_mp3('best.mp3').export('convert_best.wav', format='wav')

    def wav_to_mp3(self):
        AudioSegment.from_wav('cut_endgame.wav').export('best.mp3', format='mp3')

    def bytes_to_wav(self, source: str):
        src = source
        name = src.split('.')[0]
        self.path = f'converted_{name}.wav'
        subprocess.call(['ffmpeg', '-i', src, self.path])

    def save(self, filename: str):
        wf = wave.open(f'{filename}.wav', 'wb')
        wf.setnchannels(self.sound_info['nchannels'])
        wf.setsampwidth(self.sound_info['sampwidth'])
        wf.setframerate(self.sound_info['framerate'])
        wf.writeframes(self.content)
        wf.close()


if __name__ == '__main__':
    mt = AudioFile('../samples/convert_best.wav')
    mt.play_thread()