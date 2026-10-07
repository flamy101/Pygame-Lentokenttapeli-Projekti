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
class RouteSelectedEvent(Event):
    """A player confirmed a route during their turn."""
    name: str = field(default="Route selected event", init=False)
    route_id: str = field(init=True, repr=True)
    player_id: str = field(init=True, repr=True)


@dataclass(frozen=True, slots=True)
class CurrentPlayerChangedEvent(Event):
    """Announces whose turn is currently active."""
    name: str = field(default="Current player changed event", init=False)
    player_id: str = field(init=True, repr=True)


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
