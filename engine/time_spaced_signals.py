from functools import wraps

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


def generate_tone(freq: int, frate: int, time_vector: np.array) -> np.array:
    """
    Generates tone with frequency freq using frate for modulation

    :param frate: Input frame rate
    :param freq: Frequency of the sine wave
    :param time_vector: Input time vector
    :return: Numpy array - resulting points for sine
    """
    return 0.5 * (np.sin(2 * np.pi * freq * time_vector / frate) + 1)


def generate_one_sided_triangle(freq: int, frate: int, time_vector: np.array):
    """
    Generates one-sided triangle saw signal form

    :param freq: Frequency of triangles in one frame
    :param frate: Input frame rate
    :param time_vector: Input time vector
    :return: Numpy array - resulting points for one-sided triangle
    """
    num_of_intervals = frate // freq
    return (time_vector % num_of_intervals) / num_of_intervals


def generate_two_sided_triangle(freq: int, frate: int, time_vector: np.array):
    """
    Generates two-sided triangle saw signal form

    :param freq: Frequency of triangles in one frame
    :param frate: Input frame rate
    :param time_vector: Input time vector
    :return: Numpy array - resulting points for two-sided triangle
    """
    num_of_intervals = frate // freq
    half_interval = num_of_intervals // 2
    straight_saw = (time_vector % half_interval) / half_interval
    backward_saw = 1 - straight_saw
    output = []
    switch = False
    for frame in range(len(time_vector)):
        if not frame % half_interval:
            switch = not switch
        if switch:
            output.append(straight_saw[frame])
        else:
            output.append(backward_saw[frame])
    output[-1] = 0
    return np.array(output)


@reversed_signal
def generate_one_sided_triangle_reversed(
    freq: int, frate: int, time_vector: np.array
):
    return generate_one_sided_triangle(freq, frate, time_vector)


@reversed_signal
def generate_two_sided_triangle_reversed(
    freq: int, frate: int, time_vector: np.array
):
    return generate_two_sided_triangle(freq, frate, time_vector)


def generate_step_signal(
    freq: int, frate: int, time_vector: np.array, step_factor: float = 0.5
):
    """
    Generates step signal form

    :param step_factor: Percent of how step filled inside one frequency
    interval
    :param freq: Frequency of steps in one frame
    :param frate: Input frame rate
    :param time_vector: Input time vector
    :return: Numpy array - resulting points for step signal
    """
    num_of_intervals = frate // freq
    part_interval = num_of_intervals * step_factor
    output = []
    for frame in range(len(time_vector)):
        switch = not frame % num_of_intervals > part_interval
        if switch:
            output.append(1)
        else:
            output.append(0)
    return np.array(output)


@reversed_signal
def generate_step_signal_reversed(
    freq: int, frate: int, time_vector: np.array, step_factor: float = 0.5
):
    return generate_step_signal(freq, frate, time_vector, step_factor)


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
