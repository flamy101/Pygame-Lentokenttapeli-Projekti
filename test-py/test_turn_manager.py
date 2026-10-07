from types import SimpleNamespace

import pygame

import game_events
from controllers.route_finder import RouteFinder
from controllers.turn_manager import TurnManager
from entities.player import Player
from ui import UIManager


class Road:
    def __init__(self, road_id, node_a, node_b, cost):
        self.id = road_id
        self.node_a = node_a
        self.node_b = node_b
        self.cost = cost

    def get_other_node(self, node):
        if node == self.node_a:
            return self.node_b
        if node == self.node_b:
            return self.node_a
        raise ValueError("Node is not connected")


class EventManager:
    def __init__(self):
        self.listeners = []
        self.events = []

    def register_listener(self, listener):
        self.listeners.append(listener)

    def unregister_listener(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)

    def post(self, event):
        self.events.append(event)
        for listener in tuple(self.listeners):
            listener.notify(event)


class Assets:
    def font(self, name):
        assert name == "default"
        return pygame.font.SysFont("Arial", 18)


def test_single_player_turn_rolls_confirms_moves_charges_and_wraps():
    pygame.init()
    try:
        start = SimpleNamespace(id="A", pos_x=30, pos_y=40, name="Start")
        middle = SimpleNamespace(
            id="B", pos_x=90, pos_y=40, name="Middle", is_waypoint=True
        )
        end = SimpleNamespace(id="C", pos_x=150, pos_y=40, name="End")
        roads = {
            "ab": Road("ab", start, middle, 3),
            "bc": Road("bc", middle, end, 4),
        }
        route = SimpleNamespace(
            id="route-ab-bc",
            start_node=start,
            end_node=end,
            segments=[roads["ab"], roads["bc"]],
            route_points=[(30, 40), (90, 40), (150, 40)],
            total_cost=7,
        )
        ev_manager = EventManager()
        ui_manager = UIManager(ev_manager)
        route_finder = RouteFinder(
            ev_manager,
            nodes={node.id: node for node in (start, middle, end)},
            roads=roads,
            routes={route.id: route},
        )
        player = Player(
            id="p1",
            game_id="game-1",
            name="Player One",
            color=(200, 30, 40),
            money=100,
            current_node=start,
            current_route=None,
            route_progress=0,
            turn_order=0,
            is_eliminated=False,
            has_won=False,
            token_radius=6,
            ev_manager=ev_manager,
        )
        turn_manager = TurnManager(
            ev_manager,
            [player],
            route_finder,
            "game-1",
            ui_manager=ui_manager,
            assets=Assets(),
        )

        # A two-hop roll is looked up into one reachable route and one arrow.
        ev_manager.post(game_events.DiceRolledEvent("p1", 2, "A"))
        assert len(turn_manager.route_arrows) == 1
        arrow = turn_manager.route_arrows[0]
        arrow.on_click()
        popup = ui_manager.modal
        assert popup is not None
        assert player.current_node is start  # RouteSelected only opens the popup.

        # Confirming resolves both hops immediately, charging each road cost.
        popup.child_buttons[0].on_click()

        assert player.current_node is end
        assert player.current_route is None
        assert player.route_progress == 2
        assert player.money == 93
        assert turn_manager.current_player is player
        assert turn_manager.route_arrows == []
        assert ui_manager.modal is None
        assert game_events.TurnEndedEvent(
            previous_player_id="p1", next_player_id="p1"
        ) in ev_manager.events
    finally:
        pygame.quit()
