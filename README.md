# ReportMyTeam (Python)

A League of Legends automation tool that monitors the game client and automatically reports all players at the end of every game — except players on your friends list.

Python rewrite of the original [C# project](https://github.com/levyvix/ReportMyTeam), built with modern async Python.

## Requirements

- Windows (the League Client runs on Windows)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (dependency manager)
- League of Legends client installed and running

## Installation

### Option A — Pre-built executable

Download the latest `ReportMyTeam.exe` from the [Releases](../../releases) page. No Python required.

### Option B — Run from source

```bash
git clone https://github.com/levyvix/report-my-team-py
cd report-my-team-py
uv run report-my-team
```

## How it works

1. Detects the `LeagueClientUx` process and extracts the LCU API port and auth token
2. Fetches your friends list (friends are never reported)
3. Polls the game phase every few seconds
4. At end-of-game (`PreEndOfGame` / `EndOfGame`), fetches the stats block and reports every player who is not you and not a friend — for all 8 report categories simultaneously

## Report categories

| Category | Description |
|---|---|
| `NEGATIVE_ATTITUDE` | Negative attitude |
| `VERBAL_ABUSE` | Verbal abuse |
| `LEAVING_AFK` | Leaving / AFK |
| `ASSISTING_ENEMY_TEAM` | Assisting enemy team |
| `DISRUPTIVE_GAMEPLAY` | Disruptive gameplay |
| `HATE_SPEECH` | Hate speech |
| `THIRD_PARTY_TOOLS` | Third-party tools / cheating |
| `INAPPROPRIATE_NAME` | Inappropriate name |

## Architecture

```
src/report_my_team/
├── __main__.py      # Entry point — asyncio.TaskGroup orchestration
├── models.py        # Pydantic models for all LCU API responses
├── lcu.py           # Process detection + async HTTP client (httpx)
├── state.py         # Shared mutable state (replaces C# global statics)
├── game_monitor.py  # Phase polling + friend list fetching
└── reporter.py      # End-of-game report logic
```

Two async tasks run concurrently:
- **`monitor_client`** — watches for the LCU process, refreshes auth credentials, fetches friends
- **`monitor_phase`** — polls the game phase and triggers reporting at end-of-game

## Development

```bash
# Install dependencies
uv sync

# Run
uv run report-my-team

# Lint
uvx ruff check src/

# Format
uvx ruff format --line-length 120 src/
```

## License

MIT
