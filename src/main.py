"""Create Discord bot and stop"""

import argparse

import discord

bot = discord.Bot()  # type: ignore


@bot.command(description="List all available commands and their descriptions")  # type: ignore
async def help(context: discord.ApplicationContext) -> None:
    """
    Print help message to the user describing all commands.

    :param context: Application context
    """
    await context.respond(
        "**/help**: List all available commands and their descriptions\n"
    )


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
