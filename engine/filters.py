import numpy as np


def low_frequency_filter(
    signal: np.array,
    param: float,
):
    num_of_points = len(signal)
    filter_func = np.array(
        [1 - np.exp(-param * t / num_of_points) for t in range(num_of_points)]
    )
    return filter_func * signal


def high_frequency_filter(
    signal: np.array,
    param: float,
):
    num_of_points = len(signal)
    filter_func = np.array(
        [np.exp(-param * t / num_of_points) for t in range(num_of_points)]
    )
    return filter_func * signal


def pulse_filter(
    signal: np.array,
    param: float,
):
    num_of_points = len(signal)
    filter_func = np.array(
        [
            0.5 * (np.sin(2 * np.pi * param * t / num_of_points) + 1)
            for t in range(num_of_points)
        ]
    )
    return filter_func * signal


filter_funcs = (
    low_frequency_filter,
    high_frequency_filter,
    pulse_filter,
)
filters = tuple(func.__name__ for func in filter_funcs)
