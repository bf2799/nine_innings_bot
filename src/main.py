"""Create Discord bot and stop"""

import argparse

import discord
from discord.ext.commands.cooldowns import BucketType, Cooldown, CooldownMapping

from src.scouter import Scouter

bot = discord.Bot()  # type: ignore


@bot.command(description="List all available commands and their descriptions")  # type: ignore
async def help(context: discord.ApplicationContext) -> None:
    """
    Print help message to the user describing all commands.

    :param context: Application context
    """
    await context.respond(
        "**/help**: List all available commands and their descriptions\n"
        "**/scout** teams: Get teams from scouting database. Separate by spaces\n"
    )


@bot.command(
    description="Get PR and OVR of teams provided from scouting database",
    cooldown=CooldownMapping(Cooldown(rate=2, per=21600), BucketType.channel),
    guild_only=True,
)  # type: ignore
@discord.option("teams", description="List of teams to retrieve, separated by spaces")  # type: ignore
async def scout(
    context: discord.ApplicationContext,
    teams: str,
):
    """
    Get PR and OVR of teams provided from scouting database.

    :param context: Application context
    :param teams: List of teams to search, as space-separated strings
    """
    # Split teams by space
    team_list = teams.split(" ")
    k_max_teams = 25
    if len(team_list) > k_max_teams:
        await context.respond(
            f"Too many teams entered ({len(team_list)}). Maximum is {k_max_teams}."
        )
        return
    # Get scouting teams then format
    team_info = Scouter.read_scouting(team_list)
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

    # Read token from file
    with open(args.token_file) as tok_file:
        token: str = tok_file.readline()

    bot.run(token)
