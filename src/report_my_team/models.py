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
    summonerName: str
    championName: str | None = None


class LocalPlayer(BaseModel):
    summonerId: int


class EogStatsBlock(BaseModel):
    gameId: int
    localPlayer: LocalPlayer
    # Each team is a list of Player objects.
    # NOTE: the exact nesting field name may differ in the live LCU response.
    # Verify with a real game and adjust if needed.
    teams: list[list[Player]]


class ReportPayload(BaseModel):
    gameId: int
    categories: list[str]
    offenderSummonerId: int
    offenderPuuid: str
