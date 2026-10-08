"""Clickable route marker used to preview and select a route."""

import math
from types import SimpleNamespace

import pygame

import game_events
from ui import UIElement
from ui.confirm_travel import confirm_travel


class RouteArrow(UIElement):
    """Draw an arrow for a route and expose its nodes while hovered."""

    def __init__(
        self,
        route,
        rect,
        z_index,
        ev_manager,
        player_id,
        ui_manager=None,
        assets=None,
        player=None,
        from_node_id=None,
        to_node_id=None,
        map_view=None,
    ):
        super().__init__(rect, z_index)
        self.route = route
        self.ev_manager = ev_manager
        self.player_id = player_id
        self.from_node_id = from_node_id
        self.to_node_id = to_node_id
        self.ui_manager = ui_manager
        self.assets = assets
        self.player = player
        self.map_view = map_view
        self.current_player_id = player_id
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
        if self.map_view is not None:
            self.map_view.refresh_content()

    def on_hover_end(self):
        self.highlighted = False
        for node, previous in self._highlighted_nodes.items():
            setter = getattr(node, "set_highlighted", None)
            if setter:
                setter(previous)
            else:
                node.highlighted = previous
        self._highlighted_nodes.clear()
        if self.map_view is not None:
            self.map_view.refresh_content()

    def kill(self):
        if self.map_view is not None:
            self.map_view.remove_element(self)
        else:
            if self.ui_manager is not None and self in self.ui_manager.elements:
                self.ui_manager.remove(self)
            self.ev_manager.unregister_listener(self)

    def on_click(self):
        if self.current_player_id != self.player_id:
            return
        if self.ui_manager is None or self.assets is None:
            # Keep event-only construction usable: a scene/controller can listen
            # for this event and open the popup with its own UI dependencies.
            self.ev_manager.post(
                game_events.RouteSelectedEvent(self.route.id, self.player_id)
            )
            return

        player = self.player or SimpleNamespace(id=self.player_id)
        confirm_travel(
            self.route,
            player,
            self.ui_manager,
            self.assets,
            self.ev_manager,
        )

    def draw(self, screen):
        """Draw the supplied arrow texture toward the final route hop."""
        points = [
            (node.pos_x, node.pos_y)
            for node in self._route_nodes()
        ]
        if len(points) >= 2:
            dx = points[-1][0] - points[-2][0]
            dy = points[-1][1] - points[-2][1]
            angle = math.degrees(math.atan2(-dy, dx))
        else:
            angle = 0

        width, height = self.rect.size
        if self.assets is not None:
            source = self.assets.image("route-arrow")
            arrow = pygame.transform.smoothscale(source, (width, height)).copy()
        else:
            # Preserve event-only RouteArrow construction when no asset store is
            # supplied (for example, in controller-level use).
            arrow = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.polygon(
                arrow,
                (150, 150, 170),
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

        tint = (205, 205, 205) if self.highlighted else (185, 185, 185)
        arrow.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        # The asset points upward; subtract 90° so angle 0 points right.
        rotated = pygame.transform.rotate(arrow, angle - 90)
        screen.blit(rotated, rotated.get_rect(center=self.rect.center))
