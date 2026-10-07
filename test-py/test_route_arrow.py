import pygame

import game_events
from ui.route_arrow import RouteArrow


class Node:
    def __init__(self):
        self.highlighted = False

    def set_highlighted(self, state):
        self.highlighted = state


class Road:
    def __init__(self, node_a, node_b):
        self.node_a, self.node_b = node_a, node_b


class Route:
    id = "route-1"
    route_points = [(10, 10), (20, 10)]

    def __init__(self, nodes, reverse_roads=False):
        self.start_node = nodes[0]
        pairs = list(zip(nodes, nodes[1:]))
        if reverse_roads:
            pairs = [(b, a) for a, b in pairs]
        self.segments = [Road(a, b) for a, b in pairs]


class EventManager:
    def __init__(self):
        self.listeners = []
        self.events = []

    def register_listener(self, listener):
        self.listeners.append(listener)

    def post(self, event):
        self.events.append(event)
        for listener in self.listeners:
            listener.notify(event)


def make_arrow(reverse_roads=False):
    nodes = [Node(), Node(), Node()]
    manager = EventManager()
    route = Route(nodes, reverse_roads)
    arrow = RouteArrow(route, pygame.Rect(0, 0, 40, 20), 1, manager, "p1")
    return arrow, nodes, manager


def test_hover_highlights_route_nodes_and_restores_previous_state():
    arrow, nodes, _ = make_arrow(reverse_roads=True)
    nodes[1].highlighted = True

    arrow.on_hover_start()
    assert all(node.highlighted for node in nodes)

    arrow.on_hover_end()
    assert [node.highlighted for node in nodes] == [False, True, False]


def test_click_posts_selection_only_during_owning_players_turn():
    arrow, _, manager = make_arrow()
    arrow.on_click()
    assert manager.events == []

    manager.post(game_events.CurrentPlayerChangedEvent("p2"))
    arrow.on_click()
    assert manager.events == [game_events.CurrentPlayerChangedEvent("p2")]

    manager.post(game_events.CurrentPlayerChangedEvent("p1"))
    arrow.on_click()
    assert manager.events[-1] == game_events.RouteSelectedEvent("route-1", "p1")


def test_draw_renders_arrow():
    pygame.init()
    try:
        arrow, _, _ = make_arrow()
        screen = pygame.Surface((60, 40), pygame.SRCALPHA)
        arrow.draw(screen)
        assert screen.get_bounding_rect().width > 0
    finally:
        pygame.quit()
