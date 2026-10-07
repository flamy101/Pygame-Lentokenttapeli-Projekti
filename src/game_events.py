from dataclasses import dataclass, field
from events import Event


@dataclass(frozen=True, slots=True)
class StartGameEvent(Event):
    pass



@dataclass(frozen=True, slots=True)
class ChangeSceneEvent(Event):
    name: str = field(default="Change Scene event", init=False)
    scene_name: str = field(init=True, repr=True)



@dataclass(frozen=True, slots=True)
class SetVolume(Event):
    name: str = field(default="SetVolume", init=False)
    volume: float = field(init=True, repr=True)



@dataclass(frozen=True, slots=True)
class MapMoveEvent(Event):
    name: str = field(default="Map move event", init=False)
    dx: float = field(init=True, repr=True)
    dy: float = field(init=True, repr=True)



@dataclass(frozen=True, slots=True)
class MapScaleEvent(Event):
    name: str = field(default="Map scale event", init=False)
    zoom: float= field(init=True, repr=True)


@dataclass(frozen=True, slots=True)
class GameStartedEvent(Event):
    game_id: int
    name: str = field(default="GameStartedEvent", init=False)


@dataclass(frozen=True, slots=True)
class RouteSelectedEvent(Event):
    """A route's travel confirmation popup was opened for a player."""
    name: str = field(default="Route confirmation shown event", init=False)
    route_id: str = field(init=True, repr=True)
    player_id: str = field(init=True, repr=True)


@dataclass(frozen=True, slots=True)
class RouteConfirmedEvent(Event):
    """A player accepted travel on the route confirmation popup."""
    name: str = field(default="Route confirmed event", init=False)
    route_id: str = field(init=True, repr=True)
    player_id: str = field(init=True, repr=True)


@dataclass(frozen=True, slots=True)
class CurrentPlayerChangedEvent(Event):
    """Announces whose turn is currently active."""
    name: str = field(default="Current player changed event", init=False)
    player_id: str = field(init=True, repr=True)


@dataclass(frozen=True, slots=True)
class TurnEndedEvent(Event):
    """Signals the next player after the current turn ends."""
    name: str = field(default="Turn ended event", init=False)
    previous_player_id: int | None = field(default=None, repr=True)
    next_player_id: int | None = field(default=None, repr=True)


@dataclass(frozen=True, slots=True)
class TurnInputReadyEvent(Event):
    """The next player has taken the device and is ready to play."""
    name: str = field(default="Turn input ready event", init=False)
    player_id: int = field(init=True, repr=True)


@dataclass(frozen=True, slots=True)
class PlayerMovedEvent(Event):
    name: str = field(default="Player moved event", init=False)
    player_id: str = field(init=True, repr=True)
    from_node_id: str = field(init=True, repr=True)
    to_node_id: str = field(init=True, repr=True)


@dataclass(frozen=True, slots=True)
class PlayerArrivedEvent(Event):
    name: str = field(default="Player arrived event", init=False)
    player_id: str = field(init=True, repr=True)
    city_node_id: str = field(init=True, repr=True)


@dataclass(frozen=True, slots=True)
class PlayerEliminatedEvent(Event):
    name: str = field(default="Player eliminated event", init=False)
    player_id: str = field(init=True, repr=True)


@dataclass(frozen=True, slots=True)
class PlayerWonEvent(Event):
    name: str = field(default="Player won event", init=False)
    player_id: str = field(init=True, repr=True)


@dataclass(frozen=True, slots=True)
class DiceRolledEvent(Event):
    """A player rolled a movement value."""
    name: str = field(default="Dice rolled event", init=False)
    player_id: str = field(init=True, repr=True)
    value: int = field(init=True, repr=True)
    current_node_id: str | None = field(default=None, repr=True)

    @property
    def roll_value(self) -> int:
        """Compatibility alias used by route lookup."""
        return self.value


@dataclass(frozen=True, slots=True)
class RollRequestedEvent(Event):
    """A player's UI requested a dice roll."""
    name: str = field(default="Roll requested event", init=False)
    player_id: str = field(init=True, repr=True)
    current_node_id: str | None = field(default=None, repr=True)


@dataclass(frozen=True, slots=True)
class ReachableRoutesFoundEvent(Event):
    """Routes that can be completed within the player's roll."""
    name: str = field(default="Reachable routes found event", init=False)
    player_id: str = field(init=True, repr=True)
    routes: list = field(init=True, repr=True)
