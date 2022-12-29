"""Module that calculates win probability in Ranked Battle mode"""

import os
import pickle

import matplotlib.axis
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.widgets import Slider
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier


class RankedWinProbabilityCalculator:
    """
    Class that calculates win probability in ranked battle.

    Can train data based on csv Gear, Opponent PR, and Result of W/L/T.
    W/T/L for each opponent available via 'calc' function.
    Expected points for each opponent available via 'calc_expected_points' function.
    """

    _RANKED_RESULTS_FILENAME = "input/ranked_results.csv"
    _UNGEARED_TRAIN_FILENAME = "input/win_prob_calc_ungeared_train.pkl"
    _GEARED_TRAIN_FILENAME = "input/win_prob_calc_geared_train.pkl"

    _ungeared_log_reg: LogisticRegression | None = None
    _geared_log_reg: LogisticRegression | None = None

    # Graph persistency
    _ungeared_pr_slider = None
    _geared_pr_slider = None

    @classmethod
    def _find_train(cls, gear: bool) -> None:
        """
        Return either already-loaded train, or load from file if not loaded yet

        :param gear: Whether to find geared or ungeared train
        """
        if gear and not cls._geared_log_reg:
            if not os.path.isfile(cls._GEARED_TRAIN_FILENAME):
                raise FileNotFoundError("Neither geared train nor training file found")
            with open(cls._GEARED_TRAIN_FILENAME, "rb") as f:
                cls._geared_log_reg = pickle.load(f)
        if not gear and not cls._ungeared_log_reg:
            if not os.path.isfile(cls._UNGEARED_TRAIN_FILENAME):
                raise FileNotFoundError(
                    "Neither ungeared train nor training file found"
                )
            with open(cls._UNGEARED_TRAIN_FILENAME, "rb") as f:
                cls._ungeared_log_reg = pickle.load(f)

    @classmethod
    def train(cls) -> None:
        """Train the win probability calculator, from data in 'input/ranked_results'"""
        df = pd.read_csv("input/ranked_results.csv")

        # Ungeared train
        cls._ungeared_log_reg = LogisticRegression(max_iter=1000)
        ungeared = df[df["Gear"] == "N"]
        cls._ungeared_log_reg.fit(
            ungeared[["PR", "Opponent PR"]].to_numpy(),
            ungeared["Result"].to_numpy(),
        )
        with open(cls._UNGEARED_TRAIN_FILENAME, "wb") as f:
            pickle.dump(cls._ungeared_log_reg, f)

        # Geared Train
        cls._geared_log_reg = LogisticRegression(max_iter=1000)
        geared = df[df["Gear"] == "Y"]
        cls._geared_log_reg.fit(
            geared[["PR", "Opponent PR"]].to_numpy(), geared["Result"].to_numpy()
        )
        with open(cls._GEARED_TRAIN_FILENAME, "wb") as f:
            pickle.dump(cls._geared_log_reg, f)

    @classmethod
    def get_accuracy(cls, gear: bool) -> float:
        """
        Get accuracy of most recent trains as % of inputs correctly classified

        :param gear: Whether to get score of geared (True) or ungeared (False) train
        :return: % of inputs correctly classified
        """
        cls._find_train(gear)

        # Read data to feed into scoring function
        df = pd.read_csv("input/ranked_results.csv")
        data = df[df["Gear"] == ("Y" if gear else "N")]
        log_reg = cls._geared_log_reg if gear else cls._ungeared_log_reg
        if not log_reg:
            raise TypeError("Logistic Regression None, should contain values")
        return float(
            log_reg.score(
                data[["PR", "Opponent PR"]].to_numpy(), data["Result"].to_numpy()
            )
        )

    @classmethod
    def graph(cls, pr: int, gear: bool) -> None:
        """
        Graph win, tie, and loss probability vs opponent PR.

        :param pr: Team's power ranking
        :param gear: Team's gear status
        """
        cls._find_train(gear)

        # Calculate results for multiple PRs
        kstep = 10
        predict_data = list(range(0, 5001, kstep))
        pr_data = list(range(1165, 3801 + kstep, kstep))
        results = [cls.calc(pr, gear, predict_data) for pr in pr_data]
        fig, ax = plt.subplots(1, 1)

        def generate_traces(pr: int) -> tuple[matplotlib.axis.Axis, ...]:
            result_ = results[(pr - pr_data[0]) // kstep]

            trace_win = [100 * res[0] for res in result_]
            trace_loss = [100 * (1 - res[2]) for res in result_]

            axis1 = ax.fill_between(
                predict_data, 0, trace_win, interpolate=True, facecolor="green"
            )
            axis2 = ax.fill_between(
                predict_data, 100, trace_loss, interpolate=True, facecolor="red"
            )
            axis3 = ax.fill_between(
                predict_data,
                trace_loss,
                trace_win,
                interpolate=True,
                facecolor="lightgray",
            )

            return axis1, axis2, axis3

        win_axis, tie_axis, loss_axis = generate_traces(pr)
        ax.set_title(f"Win, Tie, Loss Probability vs PR ({'' if gear else 'No'} Gear)")
        ax.axhline(y=25, color="black", linestyle="--")
        ax.axhline(y=50, color="black", linestyle="--")
        ax.axhline(y=75, color="black", linestyle="--")
        ax.set_ylabel("Probability (%)")
        ax.set_xlabel("Power Ranking")

        def replot(pr_: int) -> None:
            nonlocal win_axis, tie_axis, loss_axis
            win_axis.remove()
            tie_axis.remove()
            loss_axis.remove()

            win_axis, tie_axis, loss_axis = generate_traces(pr_)
            fig.canvas.draw_idle()

        fig.subplots_adjust(bottom=0.25)
        ax_pr = fig.add_axes([0.1, 0.1, 0.8, 0.03])
        slider = Slider(
            ax=ax_pr,
            label="PR",
            valmin=pr_data[0],
            valmax=pr_data[-1],
            valstep=kstep,
            valinit=pr,
        )
        slider.on_changed(replot)
        if gear:
            cls._geared_pr_slider = slider
        else:
            cls._ungeared_pr_slider = slider

        win_points = [20, 14, 12, 10, 8]
        tie_points = [1, 1, 1, 1, 1]
        loss_points = [-8, -10, -12, -14, -20]
        fig2, ax2 = plt.subplots(1, 1)
        result = results[(pr - pr_data[0]) // kstep]
        for i in range(len(win_points)):
            expected_win_prob = [
                win_points[i] * res[0]
                + tie_points[i] * res[1]
                + loss_points[i] * res[2]
                for res in result
            ]
            ax2.plot(predict_data, expected_win_prob)
            try:
                crossing = predict_data[
                    np.where(np.diff(np.sign(expected_win_prob)))[0][0]
                ]
                ax2.axvline(
                    x=crossing, color="black", linestyle="--", label="_nolegend_"
                )
                ax2.text(
                    crossing - 10,
                    0.5,
                    f"PR: {crossing}",
                    horizontalalignment="right",
                    rotation=90,
                )
            except IndexError:
                continue
        ax2.set_title(f"Expected Points by Tier ({'' if gear else 'No'} Gear)")
        ax2.set_xlabel("Power Ranking")
        ax2.set_ylabel("Expected Ranked Points")
        ax2.axhline(color="black")
        ax2.legend(["+20", "+14", "+12", "+10", "+8"])

        plt.tight_layout()

    @classmethod
    def calc(cls, pr: int, gear: bool, opponent_prs: list[int]) -> list[list[float]]:
        """
        Calculate [win, tie, loss] probability against each opponent, given current PR and gear status

        :param pr: Team's power ranking
        :param gear: Whether team is using gold gear + condition drinks, or not
        :param opponent_prs: Power rankings of opponents
        :return: [win, tie, loss] probability against each opponent (x by 3 array)
        """
        cls._find_train(gear)

        log_reg = cls._geared_log_reg if gear else cls._ungeared_log_reg
        if not log_reg:
            raise TypeError("Logistic Regression None, should contain values")
        prs = [pr] * len(opponent_prs)
        results = log_reg.predict_proba(np.transpose([prs, opponent_prs]))
        win_idx = list(log_reg.classes_).index("W")
        tie_idx = list(log_reg.classes_).index("T")
        loss_idx = list(log_reg.classes_).index("L")
        return [[res[win_idx], res[tie_idx], res[loss_idx]] for res in results]

    @classmethod
    def calc_expected_points(
        cls, pr: int, gear: bool, opponent_prs: list[int], opponent_tiers: list[int]
    ) -> list[float]:
        """
        Calculate expected ranked points from playing opponents in tiers either above, at, or below your level.

        :param pr: Team's power ranking
        :param gear: Team's gear status
        :param opponent_prs: Power rankings of opponents
        :param opponent_tiers: Number of points if game won
        :return: List of expected ranked points for playing each opponent
        """
        cls._find_train(gear)

        # Check all opponent tiers are valid
        win_loss_points_dict = {
            8: -20,
            10: -14,
            12: -12,
            14: -10,
            20: -8,
            130: 13,
            120: 12,
            110: 11,
            100: 10,
        }
        if any([tier not in win_loss_points_dict.keys() for tier in opponent_tiers]):
            raise AssertionError(
                f"Invalid opponent tiers. Must be one of {list(win_loss_points_dict.keys())}"
            )

        result = cls.calc(pr, gear, opponent_prs)
        return [
            opponent_tiers[i] * res[0]
            + (1 if opponent_tiers[i] < 100 else opponent_tiers[i] / 5) * res[1]
            + win_loss_points_dict[opponent_tiers[i]] * res[2]
            for i, res in enumerate(result)
        ]


# Ranked
print("Ranked")
opponents = [2107, 2063, 2320, 1773, 274, 1020, 1568, 446, 670, 330]
expected_points = [12, 12, 12, 12, 12, 12, 12, 14, 14, 14]
RankedWinProbabilityCalculator.train()
print(RankedWinProbabilityCalculator.get_accuracy(True))
print(RankedWinProbabilityCalculator.get_accuracy(False))
expected_points = RankedWinProbabilityCalculator.calc_expected_points(
    1191, True, opponents, expected_points
)
print(expected_points)
print(sum(expected_points))

# Club
print("Club")
club_opponents = [
    785,
    1051,
    317,
    1201,
    1506,
    1985,
    1993,
    1767,
    1985,
    2287,
    1871,
    2211,
    2051,
    2860,
]
expected_club_points = [
    130,
    130,
    130,
    130,
    130,
    120,
    120,
    120,
    120,
    110,
    110,
    110,
    110,
    100,
]
expected_club_points = RankedWinProbabilityCalculator.calc_expected_points(
    1365, True, club_opponents, expected_club_points
)
print(expected_club_points)
print(sum(expected_club_points))

RankedWinProbabilityCalculator.graph(1165, True)
plt.show()
