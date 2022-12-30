"""Module that calculates GI distributions from base stats and target GI"""

import numpy as np


def calc_gi(base_stats: list[int], gi_target: int) -> list[int]:
    """
    Calculate target GI given base stats.

    :param base_stats: Base 5 stats
    :param gi_target: GI number to target
    :raises ValueError: Given base stat is outside
    :return: 5 GI stats
    """
    # Check input and raise value error if so
    if len(base_stats) != 5:
        raise ValueError(f"Only {len(base_stats)} base stats provided. Must provide 5")
    if gi_target < 0:
        raise ValueError(f"GI target {gi_target} invalid. Must be integer >= 0")
    if any([stat < 40 for stat in base_stats]):
        raise ValueError("Invalid base stats. All base stats must be at least 40")

    # Calculate GI
    initial_gi = [
        int(np.floor((stat - 40) / (sum(base_stats) - 200) * gi_target))
        for stat in base_stats
    ]
    leftover_order = np.argsort(-1 * np.array(base_stats))
    for idx in range(gi_target - sum(initial_gi)):
        initial_gi[leftover_order[idx]] += 1
    return initial_gi
