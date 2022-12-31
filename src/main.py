"""Create Discord bot and stop"""

import argparse
from datetime import datetime

import discord
from discord.ext.commands.cooldowns import BucketType, Cooldown, CooldownMapping

from src.gi_calculator import calc_gi
from src.scouter import Scouter
from src.train_probability_calculator import calc_train_probability

bot = discord.Bot()  # type: ignore


def log_user_activity(context: discord.ApplicationContext, cmd: str) -> None:
    """
    Log user activity of commands, user, and server

    :param context: Application context
    :param cmd: Command run to log
    """
    user_log.write(
        f"{cmd}: {context.user} ({context.user.display_name}) from server {context.guild}\n"
    )


@bot.command(description="List all available commands and their descriptions")  # type: ignore
async def help(context: discord.ApplicationContext) -> None:
    """
    Print help message to the user describing all commands.

    :param context: Application context
    """
    log_user_activity(context, "help")

    await context.respond(
        "**/help**: List all available commands and their descriptions\n"
        "**/scout** *teams* or *club*: Get teams or club from scouting database. Separate teams by spaces\n"
        "**/gi** *base* *target*: Calculate GI given 5 base stats separated by spaces and target GI #\n"
        "**/train_prob** *conditions* *cur_train* *level*: Calculate probability of finishing train at given level with given conditions and beginning train"
    )


@bot.command(
    description="Get PR and OVR of teams provided from scouting database",
    cooldown=CooldownMapping(Cooldown(rate=5, per=21600), BucketType.channel),
    guild_only=True,
)  # type: ignore
@discord.option("teams", description="List of teams to retrieve, separated by spaces", required=False)  # type: ignore
@discord.option("club", description="Name of club to retrieve", required=False)  # type: ignore
async def scout(
    context: discord.ApplicationContext,
    teams: str,
    club: str,
):
    """
    Get PR and OVR of teams provided from scouting database.

    :param context: Application context
    :param teams: List of teams to search, as space-separated strings
    :param club: Name of club to search
    """
    log_user_activity(context, "scout")

    # Check either teams or club were provided
    if not teams and not club:
        await context.respond("Only one input of teams/club may be provided")
        return
    if teams and club:
        club = ""

    # Split teams by space
    if teams:
        team_list = teams.split(" ")
        k_max_teams = 25
        if len(team_list) > k_max_teams:
            await context.respond(
                f"Too many teams entered ({len(team_list)}). Maximum is {k_max_teams}."
            )
            return
        # Get scouting teams then format
        team_info = Scouter.read_scouting(team_names=team_list)
    else:
        team_info = Scouter.read_scouting(club_name=club)
    border_str = "-" * 54
    header_str = f"| {'Team' : ^20} | {'Date' : ^10} | {'OVR': ^5} | {'PR': ^6} |"
    body_str = "\n".join(
        [
            f"| {info[0] : ^20} | {info[1] : ^10} | {info[2] : ^5} | {info[3] : ^6} |"
            for info in team_info
        ]
    )
    response = (
        f"```\n{border_str}\n{header_str}\n{border_str}\n{body_str}\n{border_str}\n```"
    )
    # Send formatted teams to Discord
    await context.respond(response)


@bot.command(description="Calculate GI of player from base stats")  # type: ignore
@discord.option("base", description="5 base stats, separated by spaces")  # type: ignore
@discord.option("target", type=int, description="Target GI number")  # type: ignore
async def gi(context: discord.ApplicationContext, base: str, target: int) -> None:
    """
    Calculate GI of player from base stats

    :param context: Application context
    :param base: 5 base stats, separated by spaces
    :param target: Target GI number
    """
    log_user_activity(context, "gi")

    try:
        base_stats = [int(stat) for stat in base.split(" ")]
    except ValueError:
        await context.respond("Invalid base stats. Please try again")
        return
    gi = calc_gi(base_stats=base_stats, gi_target=target)
    await context.respond(
        f"**Base Stats**: {base}\n"
        f"**GI Target**: {target}\n"
        f"**Distribution**: {', '.join([str(val) for val in gi])}\n"
    )


@bot.command(
    description="Calculate probability of finishing train with given conditions"
)  # type: ignore
@discord.option(
    "conditions",
    description="Expression of final train conditions. May include stat names (CON, POW) and joining words (and/or)",
)  # type: ignore
@discord.option(
    "cur_train",
    description="[default 0s] Current train, separated by spaces",
    default="0 0 0 0 0",
)  # type: ignore
@discord.option(
    "level", description="[default 17] Target training level", type=int, default=17
)  # type: ignore
async def train_prob(
    context: discord.ApplicationContext, conditions: str, cur_train: str, level: int
) -> None:
    """
    Command to calculate probability of finishing a train with given conditions

    :param context: Application context
    :param cur_train: Current training stats, as string of 5 space-separated integers
    :param level: Target training level
    :param conditions: Grammar-based condition to parse. May include 3-letter combo for stats
    """
    log_user_activity(context, "train_prob")

    try:
        train_stats = [int(stat) for stat in cur_train.split(" ")]
    except ValueError:
        await context.respond("Invalid training stats. Please try again")
        return
    # Acknowledge user before long calculation
    await context.respond("Calculating...")
    prob = calc_train_probability(
        cur_train=tuple(train_stats), target_level=level, condition=conditions
    )
    await context.respond(
        f"Probability that:\n"
        f"  {conditions}\n"
        f"  at level {level}\n"
        f"  starting at {cur_train}:\n"
        f"{prob * 100:.3f}% (1 in {(1/prob):.3g})"
    )


@bot.event
async def on_application_command_error(
    context: discord.ApplicationContext, error: str
) -> None:
    """
    Provide user with error.

    :param context: Application context
    :param error: Error that occurred
    """
    await context.respond(error)


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(
        prog="nine_innings_bot",
        description="General-purpose MLB 9 Innings Discord bot for data collection and ease-of-use tools",
    )
    parser.add_argument("token_file")
    args = parser.parse_args()

    # Log user action
    user_log = open(
        f"output/{datetime.now().strftime('user_activity_%m-%d-%y_%H-%M-%d.log')}", "w"
    )

    # Read token from file
    with open(args.token_file) as tok_file:
        token: str = tok_file.readline()

    bot.run(token)
    user_log.close()
