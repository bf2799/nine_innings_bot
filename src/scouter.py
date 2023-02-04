"""Module that connects to scouting database."""

import os

import numpy as np
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class Scouter(object):
    """
    Class that uses Google Sheets integration for inserting and retrieving scouting data.

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
    ) -> list[tuple[str, ...]]:
        """
        Read scouting data from Google sheets

        :param team_names: Teams to gather from scouting sheet
        :param club_name: Name of club to search. Can't have club and team name
        :raises RuntimeError: Data could not be properly attained, via connection error or other
        :return: Scouting data formatted as list of (team, date, ovr, pr)
        """
        # Try connecting. On failure, exception will be raised, and this will be exited
        if not cls._connected:
            cls._connect()
        if not cls._sheet:
            raise RuntimeError(
                "Connection to scouting database could be properly established"
            )
        # Get lowercase team names
        tuple_teams: list[tuple[str, ...]] = []
        # Try running sheet operations. If it fails, try connecting again. Total only twice
        for i in range(2):
            try:
                with open(cls._SHEET_ID_FILEPATH) as sheet_id_file:
                    sheet_id = sheet_id_file.readline()
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
                    # Sort tuple teams by PR then OVR
                    filtered_teams.sort(
                        key=lambda x: (
                            int(x[cls._COLUMNS["pr"]])
                            if x[cls._COLUMNS["pr"]].isdigit()
                            else 1e7,
                            -int(x[cls._COLUMNS["ovr"]])
                            if x[cls._COLUMNS["ovr"]].isdigit()
                            else 0,
                        )
                    )
                else:
                    filtered_teams = []
                # Turn trailing empty cells into empty strings
                for team in filtered_teams:
                    team_vals = [""] * len(cls._COLUMNS)
                    team_vals[: len(team)] = team
                    tuple_teams.append(tuple(team_vals))
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
