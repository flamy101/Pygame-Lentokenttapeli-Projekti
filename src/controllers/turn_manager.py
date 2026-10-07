"""Turn ownership and route confirmation controller for hot-seat games."""

import pygame

import game_events
from ui.route_arrow import RouteArrow


class TurnManager:
    """Own the active player and resolve confirmed routes instantly, hop by hop."""

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
            if event.player_id != self.current_player.id:
                return
            self._show_routes(event.routes)
        elif isinstance(event, game_events.RouteConfirmedEvent):
            self._confirm_route(event)

    def _show_routes(self, routes):
        self._clear_arrows()
        self.available_routes = list(routes)
        if not self.available_routes:
            self._advance_turn()
            return

        if self.ui_manager is None or self.assets is None:
            return

        for route in self.available_routes:
            arrow = RouteArrow(
                route,
                self._arrow_rect(route),
                z_index=20,
                ev_manager=self.ev_manager,
                player_id=self.current_player.id,
                ui_manager=self.ui_manager,
                assets=self.assets,
                player=self.current_player,
            )
            # The manager owns the turn value; no second event lookup is needed.
            arrow.current_player_id = self.current_player.id
            self.route_arrows.append(arrow)
            self.ui_manager.add(arrow)

    def _arrow_rect(self, route):
        points = getattr(route, "route_points", ())
        if points:
            first_x, first_y = points[0]
            next_x, next_y = points[1] if len(points) > 1 else points[0]
        else:
            first_x = getattr(route.start_node, "pos_x", 0)
            first_y = getattr(route.start_node, "pos_y", 0)
            next_x, next_y = first_x, first_y

        dx, dy = next_x - first_x, next_y - first_y
        length = (dx * dx + dy * dy) ** 0.5
        if length:
            first_x += dx / length * 18
            first_y += dy / length * 18

        if self.map_view is not None:
            scale_x = self.map_view.w / self.map_view.content_surface.get_width()
            scale_y = self.map_view.h / self.map_view.content_surface.get_height()
            first_x = self.map_view.x + first_x * scale_x
            first_y = self.map_view.y + first_y * scale_y

        rect = pygame.Rect(0, 0, 32, 22)
        rect.center = (round(first_x), round(first_y))
        return rect

    def _clear_arrows(self):
        for arrow in self.route_arrows:
            if arrow.highlighted:
                arrow.on_hover_end()
            if self.ui_manager is not None and arrow in self.ui_manager.elements:
                self.ui_manager.remove(arrow)
            unregister = getattr(self.ev_manager, "unregister_listener", None)
            if callable(unregister):
                unregister(arrow)
        self.route_arrows.clear()
        self.available_routes.clear()

    def _confirm_route(self, event):
        if event.player_id != self.current_player.id:
            return
        route = next(
            (
                candidate
                for candidate in self.available_routes
                if candidate.id == event.route_id
            ),
            None,
        )
        if route is None:
            return

        player = self.current_player
        self._clear_arrows()
        player.current_route = route
        player.route_progress = 0

        # There is no movement animation yet. Resolve every segment now; each
        # advance_one_hop charges that road's cost and applies its node effects.
        while player.current_route is route:
            if not player.advance_one_hop():
                break

        self._advance_turn()

    def _advance_turn(self):
        previous_player = self.current_player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.current_player = self.players[self.current_player_index]
        self.ev_manager.post(
            game_events.CurrentPlayerChangedEvent(self.current_player.id)
        )
        self.ev_manager.post(
            game_events.TurnEndedEvent(
                previous_player_id=previous_player.id,
                next_player_id=self.current_player.id,
            )
        )
