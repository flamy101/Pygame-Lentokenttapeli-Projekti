"""Pure lookup controller for routes affordable by a dice roll."""

from typing import Any

import game_events


class RouteFinder:
    """Find prebuilt routes that start at a node and fit a hop budget.

    Route segment records may hold ``Road`` objects directly or road IDs that
    can be resolved through ``roads``. Segment order is not assumed; each hop
    is followed from the current endpoint, which also handles roads whose
    ``node_a``/``node_b`` orientation differs from the route direction.
    """

    def __init__(self, ev_manager, nodes: dict, roads: dict, routes: dict):
        self.ev_manager = ev_manager
        self.nodes = nodes
        self.roads = roads
        self.routes = routes
        self._suppressed_rolls = set()
        ev_manager.register_listener(self)

    def suppress_next_roll(self, player_id):
        """Consume a die roll used to attempt opening a token."""
        self._suppressed_rolls.add(player_id)

    @staticmethod
    def _id(value):
        return getattr(value, "id", value)

    def _lookup(self, values: dict, key):
        if key in values:
            return values[key]
        key_id = self._id(key)
        for value in values.values():
            if self._id(value) == key_id:
                return value
        return None

    def _resolve_road(self, segment):
        if hasattr(segment, "node_a") and hasattr(segment, "node_b"):
            return segment

        road_ref = getattr(segment, "road", None)
        if road_ref is None:
            road_ref = getattr(segment, "road_id", segment)
        if hasattr(road_ref, "node_a") and hasattr(road_ref, "node_b"):
            return road_ref
        return self._lookup(self.roads, road_ref)

    def _route_fits_budget(self, route, current_node_id: Any, max_hops: int) -> bool:
        start_node = getattr(route, "start_node", None)
        if start_node is None or self._id(start_node) != self._id(current_node_id):
            return False

        segments = getattr(route, "segments", None)
        if segments is None:
            segments = getattr(route, "route_segments", ())
        remaining = list(segments)
        if not remaining:
            return False

        current_node = self._lookup(self.nodes, current_node_id) or start_node
        hops = 0
        while remaining:
            if hops >= max_hops:
                return False

            for index, segment in enumerate(remaining):
                road = self._resolve_road(segment)
                if road is None:
                    return False
                node_a = getattr(road, "node_a", None)
                node_b = getattr(road, "node_b", None)
                if self._id(node_a) == self._id(current_node):
                    current_node = node_b
                elif self._id(node_b) == self._id(current_node):
                    current_node = node_a
                else:
                    continue

                remaining.pop(index)
                hops += 1
                break
            else:
                # The route contains a disconnected segment chain.
                return False

        end_node = getattr(route, "end_node", None)
        return end_node is None or self._id(current_node) == self._id(end_node)

    def find_reachable_routes(self, current_node_id: Any, max_hops: int) -> list:
        """Return routes beginning at ``current_node_id`` within ``max_hops``."""
        if max_hops <= 0:
            return []
        return [
            route
            for route in self.routes.values()
            if self._route_fits_budget(route, current_node_id, max_hops)
        ]

    def notify(self, event):
        if isinstance(event, game_events.DiceRolledEvent):
            if event.player_id in self._suppressed_rolls:
                self._suppressed_rolls.remove(event.player_id)
                return
            reachable = self.find_reachable_routes(
                event.current_node_id, event.roll_value
            )
            self.ev_manager.post(
                game_events.ReachableRoutesFoundEvent(event.player_id, reachable)
            )
