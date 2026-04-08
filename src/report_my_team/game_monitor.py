import asyncio
import json
import logging

from .lcu import LcuClient
from .models import Friend, GameSession
from .reporter import handle_end_game
from .state import AppState

logger = logging.getLogger(__name__)

PHASE_SLEEP: dict[str, float] = {
    "Lobby": 60.0,
    "Matchmaking": 60.0,
    "ReadyCheck": 60.0,
    "ChampSelect": 60.0,
    "InProgress": 4.0,
    "WaitingForStats": 2.0,
    "PreEndOfGame": 1.0,
    "EndOfGame": 1.0,
}
DEFAULT_PHASE_SLEEP = 2.0


async def monitor_client(client: LcuClient, state: AppState) -> None:
    """Poll every 1s for the LCU process; fetch friends list when newly connected."""
    prev_connected = False
    while True:
        is_connected = client.refresh_credentials()

        if is_connected and not prev_connected:
            logger.info("League client detected. Fetching friends list...")

        if is_connected and not state.found_friends:
            await _fetch_friends(client, state)

        if not is_connected and prev_connected:
            logger.warning("League client closed. Resetting state.")
            state.reset()

        prev_connected = is_connected
        await asyncio.sleep(1.0)


async def _fetch_friends(client: LcuClient, state: AppState) -> None:
    status, body = await client.request("GET", "lol-chat/v1/friends")
    if status == 200:
        friends = [Friend.model_validate(f) for f in json.loads(body)]
        state.friends_ids = {f.summonerId for f in friends}
        state.found_friends = True
        logger.info("Loaded %d friend(s).", len(state.friends_ids))
    else:
        logger.debug("Friends fetch returned %d, will retry.", status)


async def monitor_phase(client: LcuClient, state: AppState) -> None:
    """Poll game phase and trigger end-of-game reporting."""
    while not client.is_connected or not state.found_friends:
        await asyncio.sleep(0.2)

    logger.info("Ready. Awaiting for a game to be over.")
    logger.info("------------------")

    while True:
        if not client.is_connected:
            logger.info("League client is closed.")
            await asyncio.sleep(1.0)
            continue

        status, body = await client.request("GET", "lol-gameflow/v1/session")
        if status == 200:
            session = GameSession.model_validate_json(body)
            phase = session.phase
            logger.debug("Current phase: %s", phase)

            if phase in ("PreEndOfGame", "EndOfGame"):
                await handle_end_game(client, state)

            sleep_secs = PHASE_SLEEP.get(phase, DEFAULT_PHASE_SLEEP)
        else:
            sleep_secs = DEFAULT_PHASE_SLEEP

        await asyncio.sleep(sleep_secs)
