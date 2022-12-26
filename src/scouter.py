"""Module that connects to scouting database."""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class Scouter(object):
    """
    Class that uses Google Sheets integration for inserting and retrieving scouting data.

    Class is a singleton to ensure there is only a single connection to sheet.
    """

    _SCOPES: list[str] = ["https://www.googleapis.com/auth/spreadsheets"]
    _SHEET_ID: str = "1xjdF3dZ15q_FyUYUlMa0sAiMEYTnV51_9NRJSebeD7Y"
    _CREDENTIAL_FILEPATH: str = "input/google_sheets_credentials.json"
    _TOKEN_FILEPATH: str = "input/google_sheets_token.json"
    _connected: bool = False
    _sheet = None

    _COLUMNS: dict[str, int] = {
        "team": 0,
        "date": 1,
        "ovr": 2,
        "pr": 3,
    }

    @classmethod
    def _connect(cls) -> None:
        """Connect to Google Sheets service."""
        creds = None
        if os.path.exists(cls._TOKEN_FILEPATH):
            creds = Credentials.from_authorized_user_file(
                cls._TOKEN_FILEPATH, cls._SCOPES
            )
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    cls._CREDENTIAL_FILEPATH, cls._SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(cls._TOKEN_FILEPATH, "w") as token:
                token.write(creds.to_json())

        try:
            service = build("sheets", "v4", credentials=creds)
            cls._sheet = service.spreadsheets()
            cls._connected = True
        except Exception as e:
            cls._connected = False
            raise RuntimeError("Scouter could not connect to scouting sheet") from e

    @classmethod
    def read_scouting(cls, team_names: list[str]) -> list[tuple[str, ...]]:
        """
        Read scouting data from Google sheets

        :param team_names: Teams to gather from scouting sheet
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
        lower_team_names = [name.lower() for name in team_names]
        tuple_teams: list[tuple[str, ...]] = []
        # Try running sheet operations. If it fails, try connecting again. Total only twice
        for i in range(2):
            try:
                result = (
                    cls._sheet.values()
                    .get(spreadsheetId=cls._SHEET_ID, range="Scouting!A2:D")
                    .execute()
                )
                all_values = result.get("values", [])
                filtered_teams = [
                    teams
                    for teams in [all_values][0]
                    if teams[cls._COLUMNS["team"]].lower() in lower_team_names
                ]
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
        # Sort tuple teams by PR then OVR
        tuple_teams.sort(
            key=lambda x: (
                int(x[cls._COLUMNS["pr"]]) if x[cls._COLUMNS["pr"]].isdigit() else 1e7,
                -int(x[cls._COLUMNS["ovr"]]) if x[cls._COLUMNS["ovr"]].isdigit() else 0,
            )
        )
        return tuple_teams
