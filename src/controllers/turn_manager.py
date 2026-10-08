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
        self.awaiting_token_resolution = False

        ev_manager.register_listener(self)
        player_order_str = ", ".join([f"{p.name} (ID: {p.id})" for p in self.players])
        print(f"[DEBUG] TurnManager ready. Players: [{player_order_str}]. Active player: {self.current_player.name}")

        ev_manager.post(
            game_events.CurrentPlayerChangedEvent(self.current_player.id)
        )

    def notify(self, event):
        if isinstance(event, game_events.ReachableRoutesFoundEvent):
            if self.current_player is not None and event.player_id == self.current_player.id:
                print(f"[DEBUG] ReachableRoutesFoundEvent: Found {len(event.routes)} route(s) for Player {event.player_id}")
                self._show_routes(event.routes)
            else:
                print(f"[DEBUG] Ignored ReachableRoutesFoundEvent for Player {event.player_id} (Active player is {self.current_player.id if self.current_player else 'None'})")

        elif isinstance(event, game_events.RouteConfirmedEvent):
            print(f"[DEBUG] RouteConfirmedEvent received for route {event.route_id}.")
            self._confirm_route(event)
        elif isinstance(event, game_events.TokenResolvedEvent):
            if self.current_player is not None and event.player_id == self.current_player.id:
                self.awaiting_token_resolution = False
                self._clear_arrows()
                self._advance_turn()

    def _clear_arrows(self):
        if self.route_arrows:
            print(f"[DEBUG] Clearing {len(self.route_arrows)} route arrows from map.")
        for arrow in self.route_arrows:
            if hasattr(arrow, "kill"):
                arrow.kill()
        self.route_arrows.clear()

    @staticmethod
    def _route_node_path(route):
        """Return the ordered node IDs for a route, plus whether it is connected."""
        start_node = getattr(route, "start_node", None)
        if start_node is None:
            return (), False

        node_id = lambda node: str(getattr(node, "id", node))
        path = [node_id(start_node)]
        current = start_node
        remaining = list(getattr(route, "segments", ()))
        while remaining:
            for index, road in enumerate(remaining):
                if road.node_a == current:
                    current = road.node_b
                elif road.node_b == current:
                    current = road.node_a
                else:
                    continue
                path.append(node_id(current))
                remaining.pop(index)
                break
            else:
                return tuple(path), False

        expected_end = getattr(route, "end_node", None)
        connected = expected_end is None or path[-1] == node_id(expected_end)
        return tuple(path), connected

    def _show_routes(self, routes):
        self._clear_arrows()
        self.available_routes = [
            route for route in routes
            if self.current_player is not None
            and (
                self.current_player.money >= route.total_cost
                or (
                    self.current_player.money == 0
                    and getattr(route, "road_type", None) == "sea"
                    and len(route.segments) <= 2
                )
            )
        ]
        route_paths = [
            (route, *self._route_node_path(route))
            for route in self.available_routes
        ]
        endpoint_routes = []
        for route, path, connected in route_paths:
            is_intermediate = connected and any(
                other_connected
                and len(other_path) > len(path)
                and other_path[: len(path)] == path
                for other_route, other_path, other_connected in route_paths
                if other_route is not route
            )
            if not is_intermediate:
                endpoint_routes.append(route)

        suppressed = len(self.available_routes) - len(endpoint_routes)
        self.available_routes = endpoint_routes
        if not self.available_routes:
            print("[DEBUG] No available routes found. Advancing turn...")
            self._advance_turn()
            return

        print(
            f"[DEBUG] Showing {len(self.available_routes)} route endpoint(s); "
            f"suppressed {suppressed} intermediate endpoint(s)."
        )

        if self.current_player is None:
            print("[WARNING] Active player missing; route arrows cannot be displayed.")
            return

        from_node = self.current_player.current_node
        from_node_id = from_node.id if from_node is not None else None

        for index, route in enumerate(self.available_routes):
            end_node = getattr(route, "end_node", None)
            to_node_id = end_node.id if end_node is not None else None

            arrow = RouteArrow(
                route=route,
                rect=pygame.Rect(0, 0, 48, 48),
                z_index=10,
                ev_manager=self.ev_manager,
                player_id=self.current_player.id,
                from_node_id=from_node_id,
                to_node_id=to_node_id,
                ui_manager=self.ui_manager,
                assets=self.assets,
                player=self.current_player,
                map_view=self.map_view,
            )
            arrow.suggestion_index = index
            if self.map_view is not None:
                self.map_view.add_element(arrow)
            elif self.ui_manager is not None:
                end_node = route.end_node
                arrow.rect.center = (end_node.pos_x, end_node.pos_y)
                self.ui_manager.add(arrow)
            self.route_arrows.append(arrow)

        print(f"[DEBUG] Added {len(self.route_arrows)} route arrows to the map.")

    def _confirm_route(self, event):
        if self.current_player is None or event.player_id != self.current_player.id:
            return
        route = next(
            (candidate for candidate in self.available_routes
             if str(candidate.id) == str(event.route_id)),
            None,
        )
        if route is None:
            print(f"[WARNING] Confirmed route {event.route_id} is not available.")
            return

        from_node = self.current_player.current_node
        from_node_id = from_node.id if from_node is not None else None
        path = []
        node = from_node
        try:
            for road in route.segments:
                node = road.get_other_node(node)
                path.append((road, node))
        except ValueError:
            print(f"[WARNING] Route {route.id} is disconnected from node {node.id}.")
            return

        if node != route.end_node:
            print(f"[WARNING] Route {route.id} does not end at its declared destination.")
            return

        player = self.current_player
        if not (
            player.money >= route.total_cost
            or (player.money == 0 and route.road_type == "sea" and len(route.segments) <= 2)
        ):
            print(f"[DEBUG] Player {player.id} cannot afford route {route.id}.")
            self._clear_arrows()
            self._advance_turn()
            return
        player.current_route = route
        player.route_progress = 0
        for _ in path:
            if not player.advance_one_hop():
                break
            if self.ui_manager is not None and self.ui_manager.modal is not None:
                break

        print(f"[DEBUG] Player {player.id} moved from node {from_node_id} to node {node.id}.")

        self._clear_arrows()
        if self.ui_manager is not None and self.ui_manager.modal is not None:
            self.awaiting_token_resolution = True
            return
        self._advance_turn()

    def _advance_turn(self):
        if self.current_player is None:
            return

        prev_player_id = self.current_player.id
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.current_player = self.players[self.current_player_index]

        print(f"[DEBUG] Turn Advanced: {prev_player_id} -> {self.current_player.id} ({self.current_player.name})")

        self.ev_manager.post(
            game_events.TurnEndedEvent(
                previous_player_id=prev_player_id,
                next_player_id=self.current_player.id,
            )
        )
        self.ev_manager.post(
            game_events.CurrentPlayerChangedEvent(self.current_player.id)
        )
