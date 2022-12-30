"""Module to help with calculating probabilities for trains"""
import math
from itertools import combinations
from typing import Generator

import numpy as np

from src.simple_eval import SimpleEval  # type: ignore


def exact_train_count(distribution: tuple[int, ...]) -> float:
    """
    Get count of ways for a given exact train to occur

    Probability of exact train = # ways to attain that train / # possible trains at training level.
    Let _sum = training level * 3 = sum(distribution).
    P(train) = (Training orders with repetition / possible repetitions) /  # possible trains at level
             = _sum! / (distribution[0]! * distribution[1]! * ... * distribution[4]!) / 5^(_sum)
    Here, we don't divide by 5^(_sum) to avoid dealing with tiny numbers and losing accuracy

    :param distribution: Train to get probability of, as list of 5 integers
    :return: Probability of train, as number 0 - 1
    """
    _sum = np.sum(distribution)
    possible_repetitions: list[int] = [int(math.factorial(val)) for val in distribution]
    result: int = math.factorial(_sum)
    for val in possible_repetitions:
        result //= val
    return result


def partitions(n: int, t: int) -> Generator[tuple[int, ...], None, None]:
    """
    Generate the sequences of n whole numbers that sum to t.

    :param n: Number of whole numbers (number of bins)
    :param t: Sum of integers (number of values put into bins)
    :yields: Next tuple of size n in combination
    """

    def intervals(c: tuple[int, ...]) -> Generator[int, None, None]:
        last = 0
        for i in c:
            yield i - last - 1
            last = i
        yield t + n - last - 1

    for combo in combinations(range(1, t + n), n - 1):
        yield tuple(intervals(combo))


def calc_train_probability(
    cur_train: tuple[int, ...], target_level: int, condition: str
) -> float:
    """
    Calculate probability of a train with the given condition

    :param cur_train: Current training distribution, as 5 integers
    :param target_level: Target training level. Must be no more than 20 beyond current level
    :param condition: Grammar-based condition to parse. May include 3-letter combo for stats
    :return: Probability of train occurring from 0-1
    """
    # Ensure inputs are valid
    if len(cur_train) != 5:
        raise AssertionError(
            f"Must have exactly 5 values in current train. {len(cur_train)} provided"
        )
    if any([val < 0 for val in cur_train]):
        raise AssertionError("Current train values less than 0")
    if sum(cur_train) % 3 != 0:
        raise AssertionError("Current train invalid. Must be multiple of 3")
    if not (0 <= target_level - sum(cur_train) / 3 <= 20):
        raise AssertionError(f"Target level {target_level} not between 0 and 20")

    # Replace condition stat names with variable names
    stat_var_dict = {
        "CON": "a",
        "POW": "b",
        "EYE": "c",
        "SPD": "d",
        "FLD": "e",
        "LOC": "a",
        "VEL": "b",
        "STA": "c",
        "FB": "d",
        "BRK": "e",
    }
    for key, val in stat_var_dict.items():
        condition = condition.replace(key, val)
        condition = condition.replace(key.lower(), val)

    # Create condition parser
    var_val_dict = {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0}
    condition_eval = SimpleEval(names=var_val_dict)

    sum_: float = 0.0
    cur_level = int(sum(cur_train) / 3 + 1)
    train_points_left: int = 3 * (target_level - cur_level)
    for i in partitions(5, train_points_left):
        for j, letter in enumerate(var_val_dict.keys()):
            var_val_dict[letter] = i[j] + cur_train[j]
        if condition_eval.eval(condition):
            sum_ += exact_train_count(i)

    # # Run monte carlo for verification
    # count = 0
    # trials = 100000
    # for trial in range(trials):
    #     train = list(cur_train)
    #     for _ in range(3 * (target_level - cur_level)):
    #         train[random.randrange(5)] += 1
    #     for j, letter in enumerate(var_val_dict.keys()):
    #         var_val_dict[letter] = train[j]
    #     if condition_eval.eval(condition):
    #         count += 1
    # print(count / trials)

    return sum_ / math.pow(5, train_points_left)
