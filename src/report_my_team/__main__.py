import asyncio
import logging
import sys

from report_my_team.game_monitor import monitor_client, monitor_phase
from report_my_team.lcu import LcuClient
from report_my_team.state import AppState


def _configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


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
