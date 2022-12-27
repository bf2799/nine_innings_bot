"""
Module that holds representations useful in the game or for analysis.

Includes player and team classes
"""

from dataclasses import dataclass

POSITIONS = ["C", "1B", "2B", "SS", "3B", "OF", "DH", "SP", "RP"]
PLAYER_GRADES = ["D", "G", "S", "B", "N"]
PLAYER_TYPES = ["Normal", "Sig", "Supreme", "Vintage", "Legend"]


@dataclass
class Skill:
    """
    A way to represent a skill.

    :param type: Name of skill
    :param level: Current skill level
    """

    type: str
    level: int


@dataclass
class SkillSlot:
    """
    A way to represent a skill slot

    :param level: Skill level of slot (maximum 9)
    :param skills: List of skills in the skill slot
    """

    level: int
    skills: list[Skill]


@dataclass
class Player:
    """
    Representation of a player in the game

    :param name: First and last name of player
    :param year: Year the player's card is from
    :param team: MLB team the player played for, as abbreviation
    :param grade: Card grade (ex. D for diamond, G for gold)
    :param type: Card type (ex. Sig, Normal, Prime)
    :param positions: Eligible positions
    :param base_stats: Base 5 stats
    :param gi: GI level, out of high of 90 (w/mentor)
    :param upgrade_level: Upgrade number, out of 20
    :param train: List of 5 training stats
    :param st_level: Special training level, out of 10
    :param bd: Whether card is black diamond or not
    :param lineup_stats: Final stats in a team diamond lineup
    :param main_skills: Skill slot used currently
    :param backup_skills: Secondary skill slot
    """

    name: str
    year: int
    team: str
    grade: str
    type: str
    positions: list[str]
    base_stats: list[int]
    gi: int
    upgrade_level: int
    train: list[int]
    st_level: int
    bd: bool
    lineup_stats: list[int]
    main_skills: SkillSlot | None
    backup_skills: SkillSlot | None


@dataclass
class Roster:
    """
    Representation of a team's current roster

    :param sp: 5 starting pitchers
    :param cl: Closer
    :param su: 2 set up men
    :param mr: 3 middle relievers
    :param lr: Long reliever
    :param c: Catcher
    :param b1: First baseman
    :param b2: Second baseman
    :param ss: Shortstop
    :param b3: Third baseman
    :param of: 3 outfielders
    :param dh: Designated hitter
    :param bench: 5 bench players
    """

    sp: list[Player]
    cl: Player
    su: list[Player]
    mr: list[Player]
    lr: Player
    c: Player
    b1: Player
    b2: Player
    ss: Player
    b3: Player
    of: list[Player]
    dh: Player
    bench: list[Player]


@dataclass
class Team:
    """
    Representation of a full in-game team.

    :param name: Name of team
    :param mentor_level: Level of mentor, out of 20
    :param silver_nerf: Silver skill nerfed
    :param gold_nerf: Gold skill nerfed
    :param roster: Starting roster of team
    :param reserves: List of other important players who could make the team someday
    :param points: Current amount of points currency
    :param stars: Current amount of star currency
    :param stat_amps: Current number of stat amp tickets held
    :param bds: Current number of black diamond pieces held
    :param gis: Current number of diamond grade increase tickets held
    :param girts: Current number of GI reset tickets held
    :param scts: Current number of skill change tickets held
    :param pscts: Current number of premium skill change tickets held
    :param blues: Current number of skill select change tickets held
    :param greens: Current number of skill select change tickets held
    """

    name: str
    mentor_level: int
    silver_nerf: str | None
    gold_nerf: str | None
    roster: Roster
    reserves: list[Player]
    points: int
    stars: int
    stat_amps: int
    bds: int
    gis: int
    girts: int
    scts: int
    pscts: int
    blues: int
    greens: int
