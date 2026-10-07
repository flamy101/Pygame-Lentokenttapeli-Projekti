import pygame

import events
import game_events
from controllers.turn_gate import TurnGate
from ui import UIManager


class Player:
    def __init__(self, player_id, name):
        self.id = player_id
        self.name = name


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


def test_turn_gate_uses_generic_popup_and_posts_ready_event():
    pygame.init()
    try:
        ev_manager = EventManager()
        ui_manager = UIManager(ev_manager)
        gate = TurnGate(ev_manager, ui_manager, Assets(), {2: Player(2, "Ada")})

        ev_manager.post(game_events.TurnEndedEvent(1, 2))

        popup = ui_manager.modal
        assert popup is not None
        assert popup.message == "Player Ada's turn — pass the device"
        assert len(popup.child_buttons) == 1
        ev_manager.post(events.MouseInputEvent(popup.child_buttons[0].rect.center, (1,)))

        assert ui_manager.modal is None
        assert ev_manager.events[-1] == game_events.TurnInputReadyEvent(2)
    finally:
        pygame.quit()

