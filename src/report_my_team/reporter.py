import asyncio
import logging

from .lcu import LcuClient
from .models import REPORT_CATEGORIES, EogStatsBlock, Player, ReportPayload
from .state import AppState

logger = logging.getLogger(__name__)


async def handle_end_game(client: LcuClient, state: AppState) -> None:
    status, body = await client.request("GET", "lol-end-of-game/v1/eog-stats-block")
    if status != 200:
        logger.debug("eog-stats-block returned %d, skipping.", status)
        return

    stats = EogStatsBlock.model_validate_json(body)

    if stats.gameId == state.last_game_id:
        return
    state.last_game_id = stats.gameId

    if state.current_player_id == 0:
        state.current_player_id = stats.localPlayer.summonerId
        logger.info("Identified as summoner ID %d.", state.current_player_id)

    report_tasks = [_report_player(client, state, stats.gameId, player) for team in stats.teams for player in team]
    await asyncio.gather(*report_tasks, return_exceptions=True)
    logger.info("------------------")


async def _report_player(client: LcuClient, state: AppState, game_id: int, player: Player) -> None:
    name = player.summonerName
    champ = player.championName or "Unknown"

    if player.summonerId == state.current_player_id:
        logger.info("%s (%s) is the current account, ignoring", name, champ)
        return

    if player.summonerId in state.friends_ids:
        logger.info("%s (%s) is a friend, ignoring", name, champ)
        return

    payload = ReportPayload(
        gameId=game_id,
        categories=REPORT_CATEGORIES,
        offenderSummonerId=player.summonerId,
        offenderPuuid=player.puuid,
    )
    status, _ = await client.request(
        "POST",
        "lol-player-report-sender/v1/end-of-game-reports",
        json_body=payload.model_dump(),
    )

    if status == 204:
        logger.info("%s (%s) has been reported", name, champ)
    else:
        logger.warning("Failed to report %s (%s) — HTTP %d", name, champ, status)
