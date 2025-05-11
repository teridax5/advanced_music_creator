from functools import wraps
from typing import Tuple

import numpy as np


def reversed_signal(signal):
    @wraps(signal)
    def wrapper(*args, **kwargs):
        result = signal(*args, **kwargs)
        frate = kwargs.get("frate")
        freq = kwargs.get("freq")
        if frate and freq:
            num_of_intervals = frate // freq
            switch = False
            output = []
            for idx, frame in enumerate(result):
                frame = float(frame)
                if not idx % num_of_intervals:
                    switch = not switch
                if switch:
                    output.append(0.5 * (frame + 1))
                else:
                    output.append(0.5 * (-frame + 1))
            result = np.array(output)
        return result

    return wrapper


def generate_tone(
    freq: int, frate: int, time_vector: np.array, linear_oscillator: Tuple[int]
) -> np.array:
    """
    Generates tone with frequency freq using frate for modulation

    :param frate: Input frame rate
    :param freq: Frequency of the sine wave
    :param time_vector: Input time vector
    :param linear_oscillator: FM linear oscillator
    :return: Numpy array - resulting points for sine
    """
    freq = linear_oscillator[0] * time_vector/frate + linear_oscillator[1]*freq
    return 0.5 * (np.sin(2 * np.pi * freq * time_vector / frate) + 1)


def generate_one_sided_triangle(
    freq: int, frate: int, time_vector: np.array, linear_oscillator: Tuple[int]
):
    """
    Generates one-sided triangle saw signal form

    :param freq: Frequency of triangles in one frame
    :param frate: Input frame rate
    :param time_vector: Input time vector
    :param linear_oscillator: FM linear oscillator
    :return: Numpy array - resulting points for one-sided triangle
    """
    freq = linear_oscillator[0] * time_vector/frate + linear_oscillator[1] * freq
    period = frate / freq
    return (time_vector % period) / period


def generate_two_sided_triangle(
    freq: int, frate: int, time_vector: np.array, linear_oscillator: Tuple[int]
):
    """
    Generates two-sided triangle saw signal form

    :param freq: Frequency of triangles in one frame
    :param frate: Input frame rate
    :param time_vector: Input time vector
    :param linear_oscillator: FM linear oscillator
    :return: Numpy array - resulting points for two-sided triangle
    """
    freq = linear_oscillator[0] * time_vector/frate + linear_oscillator[1] * freq
    period = frate / freq
    phase = time_vector % period

    # Создаем симметричный пилообразный сигнал
    return np.where(
        phase < period / 2,
        2 * phase / period,
        -2 * (phase - period / 2) / period + 1
    )


@reversed_signal
def generate_one_sided_triangle_reversed(
    freq: int, frate: int, time_vector: np.array, linear_oscillator: Tuple[int]
):
    return generate_one_sided_triangle(
        freq, frate, time_vector, linear_oscillator
    )


@reversed_signal
def generate_two_sided_triangle_reversed(
    freq: int, frate: int, time_vector: np.array, linear_oscillator: Tuple[int]
):
    return generate_two_sided_triangle(
        freq, frate, time_vector, linear_oscillator
    )


def generate_step_signal(
    freq: int,
    frate: int,
    time_vector: np.array,
    linear_oscillator: Tuple[int],
    step_factor: float = 0.5,
):
    """
    Generates step signal form

    :param step_factor: Percent of how step filled inside one frequency
    interval
    :param freq: Frequency of steps in one frame
    :param frate: Input frame rate
    :param time_vector: Input time vector
    :param linear_oscillator: FM linear oscillator
    :return: Numpy array - resulting points for step signal
    """
    freq = linear_oscillator[0] * time_vector/frate + linear_oscillator[1] * freq
    period = frate / freq
    return np.where(time_vector % period < period*step_factor, 1, 0)


@reversed_signal
def generate_step_signal_reversed(
    freq: int,
    frate: int,
    time_vector: np.array,
    linear_oscillator: Tuple[int],
    step_factor: float = 0.5,
):
    return generate_step_signal(
        freq, frate, time_vector, linear_oscillator, step_factor
    )


signals = (
    generate_tone,
    generate_one_sided_triangle,
    generate_one_sided_triangle_reversed,
    generate_two_sided_triangle,
    generate_two_sided_triangle_reversed,
    generate_step_signal,
    generate_step_signal_reversed,
)
signal_funcs = tuple(signal.__name__ for signal in signals)


if __name__ == "__main__":
    from gui.graphics import build_time_spaced_graphic

    num_of_points = 44100
    time_vector = np.linspace(0, num_of_points, num_of_points)
    # build_time_spaced_graphic(
    #     time_vector,
    #     generate_tone(freq=30, time_vector=time_vector)
    # )
    # build_time_spaced_graphic(
    #     time_vector,
    #     generate_one_sided_triangle(freq=30, frate=num_of_points, time_vector=time_vector)
    # )
    # build_time_spaced_graphic(
    #     time_vector,
    #     generate_two_sided_triangle(freq=10, frate=num_of_points, time_vector=time_vector)
    # )
    # build_time_spaced_graphic(
    #     time_vector,
    #     generate_step_signal(freq=10, frate=num_of_points, time_vector=time_vector)
    # )
    # build_time_spaced_graphic(
    #     time_vector,
    #     generate_one_sided_triangle_reversed(freq=30, frate=num_of_points, time_vector=time_vector)
    # )
    # build_time_spaced_graphic(
    #     time_vector,
    #     generate_two_sided_triangle_reversed(freq=10, frate=num_of_points, time_vector=time_vector)
    # )
    build_time_spaced_graphic(
        time_vector,
        generate_step_signal_reversed(
            freq=10, frate=num_of_points, time_vector=time_vector
        ),
    )
