import asyncio
import logging
import sys

from .game_monitor import monitor_client, monitor_phase
from .lcu import LcuClient
from .state import AppState


def _configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


async def _main() -> None:
    _configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("ReportMyTeam starting...")

    client = LcuClient()
    state = AppState()

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(monitor_client(client, state), name="client-monitor")
            tg.create_task(monitor_phase(client, state), name="phase-monitor")
    except* Exception as eg:
        for exc in eg.exceptions:
            logger.exception("Task failed: %s", exc)
    finally:
        await client.aclose()


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
