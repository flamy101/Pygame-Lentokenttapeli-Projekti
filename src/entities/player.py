"""Player state, route movement, and token rendering."""

from typing import Any

import pygame

import game_events


class Player:
    """A local player token and the game state needed to advance it by hops.

    ``route_progress`` is the index of the next road in ``current_route``.
    ``db_connector`` is optional; when provided it must implement
    ``apply_node_tokens(player, node)`` and may update the player's state.
    """

    def __init__(
        self,
        id: str,
        game_id: str,
        name: str,
        color: tuple[int, int, int],
        money: float,
        current_node: Any,
        current_route: Any | None,
        route_progress: int,
        turn_order: int,
        is_eliminated: bool,
        has_won: bool,
        token_radius: int,
        ev_manager,
        db_connector=None,
    ):
        self.id = id
        self.game_id = game_id
        self.name = name
        self.color = color
        self.money = money
        self.current_node = current_node
        self.current_route = current_route
        self.route_progress = route_progress
        self.turn_order = turn_order
        self.is_eliminated = is_eliminated
        self.has_won = has_won
        self.token_radius = token_radius
        self.ev_manager = ev_manager
        self.db_connector = db_connector
        self.items: dict[str, int] = {}

        # Keep the precise position as floats; pygame.Rect stores only rounded
        # integer coordinates and is updated by assignment in _sync_rect().
        node_x, node_y = self._node_position(current_node)
        self.x = float(node_x)
        self.y = float(node_y)
        self.rect = pygame.Rect(0, 0, token_radius * 2, token_radius * 2)
        self._sync_rect()

    @staticmethod
    def _node_position(node) -> tuple[float, float]:
        position = getattr(node, "screen_position", None)
        if callable(position):
            position = position()
        if position is not None:
            return float(position[0]), float(position[1])
        return float(node.pos_x), float(node.pos_y)

    def _sync_rect(self):
        """Assign rounded render coordinates without mutating Rect by floats."""
        self.rect.center = (round(self.x), round(self.y))

    def draw(self, screen: pygame.Surface):
        self._sync_rect()
        pygame.draw.circle(screen, self.color, self.rect.center, self.token_radius)

    def _apply_node_tokens(self, node):
        if self.db_connector is not None:
            apply_node_tokens = getattr(self.db_connector, "apply_node_tokens", None)
            if callable(apply_node_tokens):
                apply_node_tokens(self, node)

    def advance_one_hop(self) -> bool:
        """Move over one route road, charge its cost, and publish arrivals.

        Returns ``False`` when there is no active route or it has no remaining
        segment. Raises ``ValueError`` when route progress and current node do
        not describe a connected path.
        """
        route = self.current_route
        if route is None or self.route_progress >= len(route.segments):
            return False
        if self.is_eliminated or self.has_won:
            return False

        road = route.segments[self.route_progress]
        try:
            next_node = road.get_other_node(self.current_node)
        except ValueError as error:
            raise ValueError(
                f"Route segment {self.route_progress} is not connected to the player's current node"
            ) from error

        from_node = self.current_node
        was_eliminated = self.is_eliminated
        had_won = self.has_won

        self.money -= road.cost
        self.current_node = next_node
        self.route_progress += 1
        self.x, self.y = self._node_position(next_node)
        self._sync_rect()

        # The connector owns token lookup and applies any effects to this player.
        self._apply_node_tokens(next_node)

        arrived = next_node == route.end_node
        if arrived:
            self.current_route = None

        self.ev_manager.post(
            game_events.PlayerMovedEvent(self.id, from_node.id, next_node.id)
        )
        if not getattr(next_node, "is_waypoint", False):
            self.ev_manager.post(game_events.PlayerArrivedEvent(self.id, next_node.id))
        if not was_eliminated and self.is_eliminated:
            self.ev_manager.post(game_events.PlayerEliminatedEvent(self.id))
        if not had_won and self.has_won:
            self.ev_manager.post(game_events.PlayerWonEvent(self.id))

        return True
