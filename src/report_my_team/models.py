from pydantic import BaseModel

REPORT_CATEGORIES: list[str] = [
    "NEGATIVE_ATTITUDE",
    "VERBAL_ABUSE",
    "LEAVING_AFK",
    "ASSISTING_ENEMY_TEAM",
    "DISRUPTIVE_GAMEPLAY",
    "HATE_SPEECH",
    "THIRD_PARTY_TOOLS",
    "INAPPROPRIATE_NAME",
]


class GameSession(BaseModel):
    phase: str


class Friend(BaseModel):
    summonerId: int
    puuid: str


class Player(BaseModel):
    summonerId: int
    puuid: str
    riotIdGameName: str = ""
    championName: str | None = None
    botPlayer: bool = False


class Team(BaseModel):
    teamId: int
    players: list[Player]


class LocalPlayer(BaseModel):
    summonerId: int


class EogStatsBlock(BaseModel):
    gameId: int
    localPlayer: LocalPlayer
    teams: list[Team]


class ReportPayload(BaseModel):
    gameId: int
    categories: list[str]
    offenderSummonerId: int
    offenderPuuid: str
