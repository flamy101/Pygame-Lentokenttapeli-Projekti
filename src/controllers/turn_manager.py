"""Turn ownership and route confirmation controller for hot-seat games."""

import game_events
import pygame
from ui.route_arrow import RouteArrow


class TurnManager:
    """Own active player and resolve confirmed routes instantly."""

    def __init__(
        self,
        ev_manager,
        players,
        route_finder,
        game_id,
        ui_manager=None,
        assets=None,
        map_view=None,
    ):
        ordered_players = players.values() if isinstance(players, dict) else players
        self.players = sorted(ordered_players, key=lambda player: player.turn_order)
        if not self.players:
            raise ValueError("TurnManager requires at least one player")

        self.ev_manager = ev_manager
        self.route_finder = route_finder
        self.game_id = game_id
        self.ui_manager = ui_manager
        self.assets = assets
        self.map_view = map_view
        self.current_player_index = 0
        self.current_player = self.players[self.current_player_index]
        self.available_routes = []
        self.route_arrows: list[RouteArrow] = []

        ev_manager.register_listener(self)
        ev_manager.post(
            game_events.CurrentPlayerChangedEvent(self.current_player.id)
        )

    def notify(self, event):
        if isinstance(event, game_events.ReachableRoutesFoundEvent):
            if self.current_player is not None and event.player_id == self.current_player.id:
                self._show_routes(event.routes)
        elif isinstance(event, game_events.RouteConfirmedEvent):
            self._confirm_route(event)

    def _clear_arrows(self):
        for arrow in self.route_arrows:
            if hasattr(arrow, "kill"):
                arrow.kill()
        self.route_arrows.clear()

    def _show_routes(self, routes):
        self._clear_arrows()
        self.available_routes = list(routes)
        if not self.available_routes:
            self._advance_turn()
            return

        if self.map_view is None or self.current_player is None:
            return

        from_node = self.current_player.current_node
        from_node_id = from_node.id if from_node is not None else None

        for route in self.available_routes:
            end_node = getattr(route, "end_node", None)
            to_node_id = end_node.id if end_node is not None else None

            if hasattr(self.map_view, "add_element"):
                arrow = RouteArrow(
                    rect=pygame.Rect(0, 0, 40, 40),
                    z_index=10,
                    ev_manager=self.ev_manager,
                    player_id=self.current_player.id,
                    from_node_id=from_node_id,
                    to_node_id=to_node_id,
                    route=route,
                )
                self.map_view.add_element(arrow)
                self.route_arrows.append(arrow)

    def _confirm_route(self, event):
        route = getattr(event, "route", None)
        if route is None or self.current_player is None:
            return

        from_node = self.current_player.current_node
        from_node_id = from_node.id if from_node is not None else None
        end_node = getattr(route, "end_node", None)

        if end_node is not None:
            self.current_player.current_node = end_node
            self.ev_manager.post(
                game_events.PlayerMovedEvent(
                    player_id=self.current_player.id,
                    from_node_id=from_node_id,
                    to_node_id=end_node.id,
                )
            )

        self._clear_arrows()
        self._advance_turn()

    def _advance_turn(self):
        if self.current_player is None:
            return

        prev_player_id = self.current_player.id
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.current_player = self.players[self.current_player_index]

        self.ev_manager.post(
            game_events.TurnEndedEvent(
                previous_player_id=prev_player_id,
                next_player_id=self.current_player.id,
            )
        )
        self.ev_manager.post(
            game_events.CurrentPlayerChangedEvent(self.current_player.id)
        )