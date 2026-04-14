## Architecture

The application uses an **async event-driven architecture** with two concurrent polling tasks.

### Data flow

1. `monitor_client` (game_monitor.py) — polls every 1s for the `LeagueClientUx.exe` process; once found, fetches the friends list and sets `AppState.found_friends = True`
2. `monitor_phase` (game_monitor.py) — waits for `found_friends`, then polls `lol-gameflow/v1/session` with adaptive sleep intervals (`PHASE_SLEEP` dict: 60s in Lobby → 1s in EndOfGame)
3. When phase is `PreEndOfGame` or `EndOfGame`, calls `handle_end_game()` (reporter.py)
4. `handle_end_game` fetches `eog-stats-block`, identifies local player via `AppState.current_player_id`, and fires concurrent report tasks for all non-bot, non-friend players
5. `AppState.last_game_id` prevents duplicate reporting for the same game


### LCU API endpoints used

- `GET /lol-chat/v1/friends` — friends list
- `GET /lol-gameflow/v1/session` — current game phase
- `GET /lol-end-of-game/v1/eog-stats-block` — end-of-game stats
- `POST /lol-player-report-sender/v1/end-of-game-reports` — submit report (expects 204)
