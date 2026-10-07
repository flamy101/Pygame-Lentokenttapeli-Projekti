import pygame

import events
import game_events
from controllers.map_controller import MapController
from ui import UIManager
from ui.elements import Button
from ui.map import Map
from ui.popup import UIPopup


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


def test_popup_draws_wrapped_modal_and_exposes_only_child_buttons():
    pygame.init()
    try:
        ev_manager = EventManager()
        ui_manager = UIManager(ev_manager)
        assets = Assets()
        actions = []
        world_button = Button(pygame.Rect(120, 180, 120, 40))
        ui_manager.add(world_button)
        popup = UIPopup(
            ev_manager,
            pygame.Rect(100, 100, 420, 240),
            assets,
            "Confirm a long trip across the map before continuing",
            [("Yes", lambda: actions.append("yes")), ("Cancel", lambda: actions.append("cancel"))],
        )
        ui_manager.open_modal(popup)

        assert len(popup.child_buttons) == 2
        assert ui_manager._topmost_at(world_button.rect.center) is None
        assert ui_manager._topmost_at(popup.child_buttons[0].rect.center) is popup.child_buttons[0]
        assert ui_manager._topmost_at((105, 105)) is None

        surface = pygame.Surface((640, 480))
        surface.fill((255, 255, 255))
        popup.draw(surface)
        assert surface.get_at((10, 10))[:3] == (80, 80, 80)

        popup.child_buttons[0].on_click()
        popup.child_buttons[1].on_click()
        assert actions == ["yes", "cancel"]
        assert ev_manager.events == []

        ui_manager.close_modal()
        assert ui_manager._topmost_at(world_button.rect.center) is world_button
    finally:
        pygame.quit()


def test_map_movement_zoom_and_scroll_are_ignored_while_modal_open():
    class ModalState:
        modal = object()

    ev_manager = EventManager()
    ui_manager = ModalState()
    controller = MapController(ev_manager, ui_manager)
    controller.notify(events.KeyInputEvent("f"))
    controller.notify(events.TickEvent(1 / 60))
    assert ev_manager.events == []

    rect = pygame.Rect(10, 20, 100, 100)
    game_map = Map(
        rect,
        z_index=0,
        ev_manager=ev_manager,
        color=(0, 0, 0),
        container=pygame.Rect(0, 0, 100, 100),
        texture=pygame.Surface((100, 100)),
        ui_manager=ui_manager,
    )
    game_map.notify(game_events.MapMoveEvent(5, 5))
    game_map.notify(events.MouseScrollEvent((30, 30), 1))
    assert rect.topleft == (10, 20)
