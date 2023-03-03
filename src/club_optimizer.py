import numpy as np
from scipy.optimize import linprog

from src.win_probability_calculator import WinProbabilityCalculator

# Define the point values for wins, ties, and losses
WIN_POINTS = np.array([130, 120, 110, 100])
TIE_POINTS = np.array([26, 24, 22, 20])
LOSS_POINTS = np.array([13, 12, 11, 10])

# Define the PRs for your club's teams and the opponent club's teams
my_prs = np.array([3735, 1390, 2846, 1566, 1131])  # replace with your own data
opponent_prs = np.array([200, 300, 400, 500])  # replace with your own data

# Define the expected win, tie, and loss probabilities for each matchup
# and the opponent health values for each battle

matchup_probs = np.array(
    [WinProbabilityCalculator.calc(pr, True, opponent_prs) for pr in my_prs]
)
# matchup_probs = np.array([...])  # replace with your own data
opponent_healths = np.array(
    [np.array([1.0, 0.55, 0.3, 0.1, 0.05, 0.0]) for _ in range(opponent_prs.shape[0])]
)

# Construct the objective function to maximize expected points
print(matchup_probs.shape)
print(opponent_healths.shape)
objective = (
    -np.concatenate([WIN_POINTS, TIE_POINTS, LOSS_POINTS])
    @ (matchup_probs * opponent_healths).ravel()
)

# Define the constraints to ensure each team plays a unique opponent in each battle
n_teams = my_prs.size
n_opponents = opponent_prs.size
constraints = []
for i in range(n_teams):
    for j in range(n_opponents):
        A = np.zeros((3, n_teams * n_opponents))
        A[:, i * n_opponents + j] = 1
        b = np.ones(3)
        constraints.append({"type": "ineq", "fun": lambda x, A=A, b=b: b - A @ x})

# Add a new constraint that doubles the expected points if the total opponent health reduction is greater than 15
coeff = 2.0
constraints.append(
    {
        "type": "ineq",
        "fun": lambda x: objective @ x
        - (1 + (opponent_healths * x.reshape(n_teams, n_opponents)).sum() > 2.8)
        * coeff
        * objective
        @ x,
    }
)

# Solve the linear program to get the optimal matchup assignments
bounds = [(0, 1)] * (n_teams * n_opponents)
result = linprog(
    c=objective,
    A_ub=[c["fun"] for c in constraints],
    b_ub=[0] * len(constraints),
    bounds=bounds,
)

# Reshape the solution into a matrix of matchup assignments
matchup_assignments = result.x.reshape(n_teams, n_opponents)

print(matchup_assignments)
