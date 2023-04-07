"""Module that connects to scouting database."""
import abc
import json
import os
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


@dataclass
class TeamInfo:
    """Format of team info after scouting."""

    team: str
    date: datetime
    ovr: float | None
    pr: int | None


class Scouter(abc.ABC):
    """Interface for a scouter."""

    @classmethod
    @abc.abstractmethod
    def read_scouting(
        cls, team_names: None | list[str] = None, club_name: None | str = None
    ) -> list[TeamInfo]:
        """
        Function interface for reading scouting. Given team names or club names, provide a list of team info.

        :param team_names: List of teams to get info on
        :param club_name: Club name to get info on
        """
        pass


class GoogleSheetsScoutingQuery(Scouter):
    """
    Class that uses Google Sheets integration for retrieving scouting data.

    Class is a singleton to ensure there is only a single connection to sheet.
    """

    _SCOPES: list[str] = ["https://www.googleapis.com/auth/spreadsheets"]
    _SHEET_ID_FILEPATH = "input/scouter_google_sheet_id.txt"
    _SERVICE_ACCOUNT_FILEPATH: str = "input/google_service_account.json"
    _connected: bool = False
    _sheet = None

    _COLUMNS: dict[str, int] = {
        "team": 0,
        "date": 1,
        "ovr": 2,
        "pr": 3,
        "club": 4,
    }

    @classmethod
    def _connect(cls) -> None:
        """Connect to Google Sheets service."""
        if not os.path.exists(cls._SERVICE_ACCOUNT_FILEPATH):
            raise FileNotFoundError(
                f"Couldn't find service account file {cls._SERVICE_ACCOUNT_FILEPATH}"
            )
        try:
            creds = Credentials.from_service_account_file(
                cls._SERVICE_ACCOUNT_FILEPATH, scopes=cls._SCOPES
            )
            service = build("sheets", "v4", credentials=creds)
            cls._sheet = service.spreadsheets()
            cls._connected = True
        except Exception as e:
            cls._connected = False
            raise RuntimeError("Scouter could not connect to scouting sheet") from e

    @classmethod
    def read_scouting(
        cls, team_names: None | list[str] = None, club_name: None | str = None
    ) -> list[TeamInfo]:
        """
        Read scouting data from Google sheets

        :param team_names: Teams to gather from scouting sheet
        :param club_name: Name of club to search. Can't have club and team name
        :raises RuntimeError: Data could not be properly attained, via connection error or other
        :return: Scouting data formatted as list of TeamInfo
        """
        # Try connecting. On failure, exception will be raised, and this will be exited
        if not cls._connected:
            cls._connect()
        if not (cls._connected and cls._sheet):
            raise RuntimeError(
                "Connection to scouting database could be properly established"
            )
        # Get lowercase team names
        tuple_teams: list[TeamInfo] = []
        # Try running sheet operations. If it fails, try connecting again. Total only twice
        for i in range(2):
            try:
                with open(cls._SHEET_ID_FILEPATH) as sheet_id_file:
                    sheet_id = sheet_id_file.readline().strip("\n")
                result = (
                    cls._sheet.values()
                    .get(spreadsheetId=sheet_id, range="Scouting!A2:E")
                    .execute()
                )
                all_values = result.get("values", [])
                if team_names:
                    # Get teams from sheet also in team list
                    team_names_lower = [name.lower() for name in team_names]
                    filtered_teams = [
                        teams
                        for teams in [all_values][0]
                        if teams[cls._COLUMNS["team"]].lower().strip()
                        in team_names_lower
                    ]
                    # Sort by entered team orders
                    filtered_team_idxs = [
                        team_names_lower.index(
                            team[cls._COLUMNS["team"]].lower().strip()
                        )
                        for team in filtered_teams
                    ]
                    filtered_teams = list(
                        np.array(filtered_teams, dtype=object)[
                            np.argsort(filtered_team_idxs)
                        ]
                    )
                elif club_name:
                    filtered_teams = [
                        teams
                        for teams in [all_values][0]
                        if len(teams) > cls._COLUMNS["club"]
                        and teams[cls._COLUMNS["club"]].lower() == club_name.lower()
                    ]
                else:
                    filtered_teams = []
                # Turn trailing empty cells into empty strings
                for team in filtered_teams:
                    team_vals = [""] * len(cls._COLUMNS)
                    team_vals[: len(team)] = team
                    team_info = TeamInfo(
                        team=team_vals[cls._COLUMNS["team"]],
                        date=datetime.strptime(
                            team_vals[cls._COLUMNS["date"]], "%m/%d/%Y"
                        ),
                        ovr=float(team_vals[cls._COLUMNS["ovr"]])
                        if team_vals[cls._COLUMNS["ovr"]].replace(".", "").isdigit()
                        else None,
                        pr=int(team_vals[cls._COLUMNS["pr"]])
                        if team_vals[cls._COLUMNS["pr"]].isdigit()
                        else None,
                    )
                    tuple_teams.append(team_info)
                # Stop after first attempt if successful
                break
            except Exception:
                cls._connect()
        # Tell user if connection failed
        if not cls._connected:
            raise RuntimeError(
                "Connection to scouting database could be properly established"
            )
        if not tuple_teams:
            raise RuntimeWarning("No given teams found in database")
        return tuple_teams


class SddctScoutingQuery(Scouter):
    """Class to scout teams from sddct.com API."""

    _QUERY_KEY_FILEPATH = "input/sddct_query_key.txt"

    @classmethod
    def read_scouting(
        cls, team_names: None | list[str] = None, club_name: None | str = None
    ) -> list[TeamInfo]:
        """
        Read scouting data from SDDCT.com

        :param team_names: Teams to gather from scouting site
        :param club_name: Name of club to search. Can't have club and team name
        :return: Scouting data formatted as list of TeamInfo
        """
        # Verify inputs
        if team_names is None and club_name is None:
            return []
        # Read key
        with open(cls._QUERY_KEY_FILEPATH) as key_file:
            key = key_file.readline().strip("\n")
        # Get data from SDDCT
        js_input = {
            "key": key,
            "mode": "teams" if team_names else "club",
            "data": club_name
            if club_name
            else ",".join(team_names)
            if team_names
            else "",
        }
        response = requests.post("https://api.dct.nyc/mlb9i/mlbquery", json=js_input)
        response_json = json.loads(response.text)
        lower_team_names = (
            [] if not team_names else [name.lower() for name in team_names]
        )
        team_info = [
            TeamInfo(
                team=team["team"],
                date=datetime.strptime(str(team["date"]), "%Y%m%d"),
                ovr=float(team["ovr"])
                if team["ovr"].replace(".", "").isdigit()
                else None,
                pr=int(team["pr"]) if str(team["pr"]).isdigit() else None,
            )
            for team in response_json
            if club_name or team["team"].lower() in lower_team_names
        ]
        return team_info


class MainScouter(Scouter):
    """
    Class that queries from all available locations for retrieving scouting data.

    Class is a singleton to ensure there is only a single connection to sheet.
    Once data from multiple sources is retrieved, it's combined to keep newer data.
    """

    @classmethod
    def read_scouting(
        cls, team_names: None | list[str] = None, club_name: None | str = None
    ) -> list[TeamInfo]:
        """
        Read scouting data from all sources.

        :param team_names: Teams to gather from scouting sources
        :param club_name: Name of club to search. Can't have club and team name
        :return: Scouting data formatted as list of TeamInfo
        """
        # Stop if no input provided
        if not team_names and not club_name:
            return []

        # Get teams in club from all sources if club provided
        all_team_names: list[str] = []
        if club_name and not team_names:
            for scouter1 in [GoogleSheetsScoutingQuery]:
                teams = scouter1.read_scouting(club_name=club_name)
                all_team_names = all_team_names + [team.team for team in teams]
            unique_team_names = []
            for x in all_team_names:
                if x.lower() not in unique_team_names:
                    unique_team_names.append(x.lower())
            all_team_names = unique_team_names

        # Gather all teams and ensure no duplicate team names remain at end
        elif team_names:
            all_team_names = team_names

        # Scout teams
        existing_teams: list[TeamInfo] = []
        existing_team_names: list[str] = []
        for scouter2 in [GoogleSheetsScoutingQuery, SddctScoutingQuery]:
            cur_teams = scouter2.read_scouting(team_names=all_team_names)
            # Loop through all teams in current scouter
            for cur_team in cur_teams:
                # If current team already in existing teams, update OVR, PR, and date accordingly
                if cur_team.team.lower() in existing_team_names:
                    compare_team_idx = existing_team_names.index(cur_team.team.lower())
                    compare_team = existing_teams[compare_team_idx]
                    # OVR is highest OVR that isn't None
                    existing_teams[compare_team_idx].ovr = max(
                        list(filter(None, [compare_team.ovr, cur_team.ovr]))
                    )
                    # PR is newest available PR
                    if cur_team.pr and (
                        cur_team.date > existing_teams[compare_team_idx].date
                        or not existing_teams[compare_team_idx].pr
                    ):
                        existing_teams[compare_team_idx].pr = cur_team.pr
                    # Date is newest date
                    existing_teams[compare_team_idx].date = max(
                        existing_teams[compare_team_idx].date, cur_team.date
                    )
                # If current team not already in existing teams, just add it
                else:
                    existing_teams.append(cur_team)
                    existing_team_names.append(cur_team.team.lower())
        # If club was provided, sort output by PR and OVR
        if club_name:
            existing_teams.sort(
                key=lambda x: (
                    x.pr if x.pr else 1e7,
                    -x.ovr if x.ovr else 0,
                )
            )
        # Otherwise, sort by team name provided
        elif team_names:
            lower_team_names = [name.lower() for name in team_names]
            existing_teams.sort(key=lambda x: (lower_team_names.index(x.team.lower())))

        return existing_teams
