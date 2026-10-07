import game_events
import pygame
import events


class MapController:

    SPEED = 300

    def __init__(self, ev_manager, ui_manager=None):

        self.ev_manager = ev_manager
        self.ui_manager = ui_manager
        ev_manager.register_listener(self)

    def _modal_is_open(self):
        return self.ui_manager is not None and self.ui_manager.modal is not None

    def notify(self, event):
        if self._modal_is_open() and isinstance(
            event,
            (events.TickEvent, events.KeyInputEvent, events.MouseScrollEvent),
        ):
            return

        match event:
            case events.TickEvent():
                if not pygame.display.get_init():
                    return
                keys = pygame.key.get_pressed()
                vel_dx = (keys[pygame.K_d] - keys[pygame.K_a]) * self.SPEED * event.dt * -1
                vel_dy = (keys[pygame.K_s] - keys[pygame.K_w]) * self.SPEED * event.dt * -1

                if vel_dx or vel_dy:
                    self.ev_manager.post(game_events.MapMoveEvent(vel_dx, vel_dy))

            case events.KeyInputEvent():
                key = event.unicodechar
                if key == "r" or "f":
                    match key:
                        case "r":
                            zoom = 0.9
                            self.ev_manager.post(game_events.MapScaleEvent(zoom))
                        case "f":
                            zoom = 1.1
                            self.ev_manager.post(game_events.MapScaleEvent(zoom))

            case events.MouseScrollEvent():
                # Map applies cursor-anchored zoom after receiving this event.
                return
