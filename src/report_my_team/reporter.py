import asyncio
import logging

from report_my_team.lcu import LcuClient
from report_my_team.models import REPORT_CATEGORIES, EogStatsBlock, Player, ReportPayload
from report_my_team.state import AppState

logger = logging.getLogger(__name__)


async def handle_end_game(client: LcuClient, state: AppState) -> None:
    logger.info("End of game reached. Fetching stats...")
    status, body = await client.request("GET", "lol-end-of-game/v1/eog-stats-block")
    if status != 200:
        logger.debug("eog-stats-block returned %d, skipping.", status)
        return

    stats = EogStatsBlock.model_validate_json(body)

    if stats.gameId == state.last_game_id:
        logger.debug("Game %d already processed, skipping.", stats.gameId)
        return
    state.last_game_id = stats.gameId

    if state.current_player_id == 0:
        state.current_player_id = stats.localPlayer.summonerId
        logger.info("Identified as summoner ID %d.", state.current_player_id)

    player_count = sum(len(team) for team in stats.teams)
    logger.info("Game %d ended. Processing %d players...", stats.gameId, player_count)

    report_tasks = [_report_player(client, state, stats.gameId, player) for team in stats.teams for player in team]
    await asyncio.gather(*report_tasks, return_exceptions=True)
    logger.info("------------------")


async def _report_player(client: LcuClient, state: AppState, game_id: int, player: Player) -> None:
    name = player.summonerName
    champ = player.championName or "Unknown"

    if player.summonerId == state.current_player_id:
        logger.info("Skipping %s (%s) — current account", name, champ)
        return

    if player.summonerId in state.friends_ids:
        logger.info("Skipping %s (%s) — friend detected (ID %d)", name, champ, player.summonerId)
        return

    logger.info("Reporting %s (%s, ID %d)...", name, champ, player.summonerId)
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
