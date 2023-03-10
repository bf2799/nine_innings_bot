# MLB 9 Innings Discord Bot

General-purpose MLB 9 Innings Discord bot for data collection and ease-of-use tools.

## Discord Commands

| Command              | Description                                                               |
|----------------------|---------------------------------------------------------------------------|
| /help                | List all available commands and their descriptions                        |
| /scout teams or club | Get scouting data for all teams or club listed. Teams separated by spaces |
| /gi base target      | Calculate GI given 5 base stats separated by spaces and target GI #       |
| /train_prob conditions cur_train level | Calculate probability of finishing train at given level with given conditions and beginning train |

## Future Behaviors

- GI calculation at levels
- Train finish helper command
- Give Advice Command
- PR vs PR win probability
- Insert scouting data
- Query scouting data

## Developer Overview

This bot was written in Python, primarily using the *py-cord* library.
A general-purpose setup shell script is included for developer ease of setup. Run `./install_setup.sh` to set up
