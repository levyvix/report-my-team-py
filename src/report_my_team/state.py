from dataclasses import dataclass, field


@dataclass
class AppState:
    last_game_id: int = 0
    current_player_id: int = 0
    friends_ids: set[int] = field(default_factory=set)
    found_friends: bool = False

    def reset(self) -> None:
        """Reset state when the League client closes."""
        self.current_player_id = 0
        self.friends_ids.clear()
        self.found_friends = False
