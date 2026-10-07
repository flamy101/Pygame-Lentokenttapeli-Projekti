import game_events
from controllers.route_finder import RouteFinder


class Node:
    def __init__(self, node_id):
        self.id = node_id
        self.pos_x = 0
        self.pos_y = 0


class Road:
    def __init__(self, road_id, node_a, node_b):
        self.id = road_id
        self.node_a = node_a
        self.node_b = node_b


class Route:
    def __init__(self, route_id, start_node, end_node, segments):
        self.id = route_id
        self.start_node = start_node
        self.end_node = end_node
        self.segments = segments


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


def make_finder():
    a, b, c, d = (Node(node_id) for node_id in ("A", "B", "C", "D"))
    roads = {
        "ab": Road("ab", a, b),
        # Deliberately reversed endpoint direction and unordered route chain.
        "bc": Road("bc", c, b),
        "cd": Road("cd", c, d),
    }
    routes = {
        "ab": Route("ab", a, b, [roads["ab"]]),
        "ac": Route("ac", a, c, [roads["bc"], roads["ab"]]),
        "ad": Route("ad", a, d, [roads["cd"], roads["ab"], roads["bc"]]),
        "bd": Route("bd", b, d, [roads["bc"], roads["cd"]]),
        "broken": Route("broken", a, d, [roads["ab"], roads["cd"]]),
    }
    manager = EventManager()
    finder = RouteFinder(manager, {n.id: n for n in (a, b, c, d)}, roads, routes)
    return finder, manager, routes


def test_reachable_routes_respect_hop_budgets():
    finder, _, routes = make_finder()

    assert finder.find_reachable_routes("A", 1) == [routes["ab"]]
    assert finder.find_reachable_routes("A", 2) == [routes["ab"], routes["ac"]]
    assert finder.find_reachable_routes("A", 3) == [
        routes["ab"],
        routes["ac"],
        routes["ad"],
    ]
    assert finder.find_reachable_routes("A", 0) == []
    assert finder.find_reachable_routes("missing", 3) == []


def test_dice_roll_posts_reachable_routes_for_rolling_player():
    finder, manager, routes = make_finder()
    dice_event = game_events.DiceRolledEvent("p1", 2, "A")

    manager.post(dice_event)

    assert manager.events[-1] == game_events.ReachableRoutesFoundEvent(
        "p1", [routes["ab"], routes["ac"]]
    )
