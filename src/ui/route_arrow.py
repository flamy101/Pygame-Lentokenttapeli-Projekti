"""Clickable route marker used to preview and select a route."""

import math

import pygame

import game_events
from ui import UIElement


class RouteArrow(UIElement):
    """Draw an arrow for a route and expose its nodes while hovered."""

    def __init__(self, route, rect, z_index, ev_manager, player_id):
        super().__init__(rect, z_index)
        self.route = route
        self.ev_manager = ev_manager
        self.player_id = player_id
        self.current_player_id = None
        self._highlighted_nodes = {}
        ev_manager.register_listener(self)

    def notify(self, event):
        if isinstance(event, game_events.CurrentPlayerChangedEvent):
            self.current_player_id = event.player_id

    def _route_nodes(self):
        nodes = [self.route.start_node]
        remaining = list(self.route.segments)
        current = self.route.start_node

        # Road endpoint orientation does not necessarily match route direction.
        while remaining:
            for index, road in enumerate(remaining):
                if road.node_a == current:
                    current = road.node_b
                elif road.node_b == current:
                    current = road.node_a
                else:
                    continue
                if current not in nodes:
                    nodes.append(current)
                remaining.pop(index)
                break
            else:
                # Also highlight every endpoint if the route data is disconnected.
                for road in remaining:
                    for node in (road.node_a, road.node_b):
                        if node not in nodes:
                            nodes.append(node)
                break

        return nodes

    def on_hover_start(self):
        self.highlighted = True
        for node in self._route_nodes():
            previous = getattr(node, "highlighted", False)
            self._highlighted_nodes[node] = previous
            setter = getattr(node, "set_highlighted", None)
            if setter:
                setter(True)
            else:
                node.highlighted = True

    def on_hover_end(self):
        self.highlighted = False
        for node, previous in self._highlighted_nodes.items():
            setter = getattr(node, "set_highlighted", None)
            if setter:
                setter(previous)
            else:
                node.highlighted = previous
        self._highlighted_nodes.clear()

    def on_click(self):
        if self.current_player_id != self.player_id:
            return
        self.ev_manager.post(
            game_events.RouteSelectedEvent(self.route.id, self.player_id)
        )

    def draw(self, screen):
        """Draw an arrow rotated toward the first segment of the route."""
        points = self.route.route_points
        if len(points) >= 2:
            dx = points[1][0] - points[0][0]
            dy = points[1][1] - points[0][1]
            angle = math.degrees(math.atan2(-dy, dx))
        else:
            angle = 0

        color = (255, 220, 70) if self.highlighted else (245, 245, 245)
        width, height = self.rect.size
        arrow = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.polygon(
            arrow,
            color,
            [
                (0, height * 0.25),
                (width * 0.58, height * 0.25),
                (width * 0.58, 0),
                (width, height * 0.5),
                (width * 0.58, height),
                (width * 0.58, height * 0.75),
                (0, height * 0.75),
            ],
        )
        rotated = pygame.transform.rotate(arrow, angle)
        screen.blit(rotated, rotated.get_rect(center=self.rect.center))
