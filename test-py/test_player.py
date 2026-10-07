import pygame

import game_events
from entities.player import Player
from entities.token import Token


class Node:
    def __init__(self, node_id, x, y, is_waypoint=False):
        self.id = node_id
        self.pos_x = x
        self.pos_y = y
        self.is_waypoint = is_waypoint


class Road:
    def __init__(self, node_a, node_b, cost):
        self.node_a = node_a
        self.node_b = node_b
        self.cost = cost

    def get_other_node(self, node):
        if node == self.node_a:
            return self.node_b
        if node == self.node_b:
            return self.node_a
        raise ValueError("Node is not connected to this road")


class Route:
    def __init__(self, start_node, end_node, roads):
        self.start_node = start_node
        self.end_node = end_node
        self.segments = roads


class EventManager:
    def __init__(self):
        self.events = []

    def register_listener(self, listener):
        pass

    def post(self, event):
        self.events.append(event)


class DBConnector:
    def __init__(self, effect=None):
        self.nodes_checked = []
        self.effect = effect

    def apply_node_tokens(self, player, node):
        self.nodes_checked.append(node.id)
        if self.effect:
            self.effect(player, node)


def make_player(*, db_connector=None):
    start = Node("start", 10.25, 20.25)
    waypoint = Node("waypoint", 11.25, 21.25, is_waypoint=True)
    destination = Node("destination", 12.25, 22.25)
    route = Route(start, destination, [Road(start, waypoint, 2), Road(waypoint, destination, 3)])
    manager = EventManager()
    player = Player(
        id="p1",
        game_id="g1",
        name="Player 1",
        color=(20, 80, 200),
        money=10,
        current_node=start,
        current_route=route,
        route_progress=0,
        turn_order=0,
        is_eliminated=False,
        has_won=False,
        token_radius=5,
        ev_manager=manager,
        db_connector=db_connector,
    )
    return player, manager


def test_advance_one_hop_updates_node_cost_and_movement_event():
    connector = DBConnector()
    player, manager = make_player(db_connector=connector)

    assert player.advance_one_hop()

    assert player.money == 8
    assert player.current_node.id == "waypoint"
    assert player.route_progress == 1
    assert player.current_route is not None
    assert connector.nodes_checked == ["waypoint"]
    assert (player.x, player.y) == (11.25, 21.25)
    assert player.rect.center == (11, 21)
    assert manager.events == [game_events.PlayerMovedEvent("p1", "start", "waypoint")]


def test_arrival_at_city_clears_route_and_posts_arrival_event():
    player, manager = make_player()
    player.advance_one_hop()

    assert player.advance_one_hop()

    assert player.money == 5
    assert player.current_node.id == "destination"
    assert player.current_route is None
    assert player.route_progress == 2
    assert manager.events[-2:] == [
        game_events.PlayerMovedEvent("p1", "waypoint", "destination"),
        game_events.PlayerArrivedEvent("p1", "destination"),
    ]


def test_arriving_at_node_applies_and_claims_its_token():
    player, _ = make_player()
    destination = player.current_route.segments[0].node_b
    token = Token(
        id="token-1",
        token_type="bonus",
        category="money",
        money_delta=5,
        texture=pygame.Surface((8, 8), pygame.SRCALPHA),
    )
    destination.tokens = [token]

    assert player.advance_one_hop()

    assert player.money == 13
    assert token.is_claimed


def test_fractional_player_position_is_preserved_across_rect_updates():
    player, _ = make_player()
    for _ in range(4):
        player.x += 0.25
        player._sync_rect()

    assert player.x == 11.25
    assert player.rect.centerx == 11


def test_win_and_elimination_effects_emit_events():
    def effect(player, node):
        if node.id == "waypoint":
            player.is_eliminated = True
            player.has_won = True

    player, manager = make_player(db_connector=DBConnector(effect))
    player.advance_one_hop()

    assert manager.events[-2:] == [
        game_events.PlayerEliminatedEvent("p1"),
        game_events.PlayerWonEvent("p1"),
    ]
    assert not player.advance_one_hop()


def test_draw_uses_integer_rect_center_without_losing_float_position():
    pygame.init()
    try:
        player, _ = make_player()
        player.x = 10.75
        player.y = 20.75
        player.draw(pygame.Surface((40, 40)))
        assert (player.x, player.y) == (10.75, 20.75)
        assert player.rect.center == (11, 21)
    finally:
        pygame.quit()
