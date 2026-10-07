from types import SimpleNamespace

import pygame

import game_events
from ui import UIManager
from ui.route_arrow import RouteArrow


class EventManager:
    def __init__(self):
        self.listeners = []
        self.events = []

    def register_listener(self, listener):
        self.listeners.append(listener)

    def post(self, event):
        self.events.append(event)
        for listener in tuple(self.listeners):
            listener.notify(event)


class Assets:
    def font(self, name):
        assert name == "default"
        return pygame.font.SysFont("Arial", 20)


def make_route():
    end_node = SimpleNamespace(id="city-2", name="Lagos")
    return SimpleNamespace(
        id="route-1",
        end_node=end_node,
        total_cost=125,
        start_node=SimpleNamespace(id="city-1"),
        segments=[],
        route_points=[],
    )


def test_route_arrow_opens_confirmation_and_yes_posts_confirmed_event():
    pygame.init()
    try:
        ev_manager = EventManager()
        ui_manager = UIManager(ev_manager)
        arrow = RouteArrow(
            make_route(),
            pygame.Rect(0, 0, 40, 20),
            1,
            ev_manager,
            "p1",
            ui_manager=ui_manager,
            assets=Assets(),
            player=SimpleNamespace(id="p1"),
        )
        ev_manager.post(game_events.CurrentPlayerChangedEvent("p1"))

        arrow.on_click()

        popup = ui_manager.modal
        assert popup is not None
        assert popup.message == "Travel to Lagos for £125?"
        assert len(popup.child_buttons) == 2
        assert ev_manager.events[-1] == game_events.RouteSelectedEvent("route-1", "p1")
        assert not any(isinstance(event, game_events.RouteConfirmedEvent) for event in ev_manager.events)

        popup.child_buttons[0].on_click()

        assert ui_manager.modal is None
        assert ev_manager.events[-1] == game_events.RouteConfirmedEvent("route-1", "p1")
    finally:
        pygame.quit()


def test_cancel_closes_route_confirmation_without_confirming():
    pygame.init()
    try:
        ev_manager = EventManager()
        ui_manager = UIManager(ev_manager)
        arrow = RouteArrow(
            make_route(),
            pygame.Rect(0, 0, 40, 20),
            1,
            ev_manager,
            "p1",
            ui_manager=ui_manager,
            assets=Assets(),
            player=SimpleNamespace(id="p1"),
        )
        ev_manager.post(game_events.CurrentPlayerChangedEvent("p1"))
        arrow.on_click()
        popup = ui_manager.modal
        assert popup is not None

        popup.child_buttons[1].on_click()

        assert ui_manager.modal is None
        assert not any(isinstance(event, game_events.RouteConfirmedEvent) for event in ev_manager.events)
    finally:
        pygame.quit()
