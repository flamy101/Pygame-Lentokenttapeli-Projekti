"""Helpers for confirming a player's route travel."""

import pygame

import game_events
from ui.popup import UIPopup


def confirm_travel(route, player, ui_manager, assets, ev_manager):
    """Open the Yes/Cancel popup for a route and announce that it was shown."""
    screen = pygame.display.get_surface()
    screen_size = screen.get_size() if screen is not None else (1200, 900)
    width = max(1, min(480, screen_size[0] - 24))
    height = max(1, min(220, screen_size[1] - 24))
    rect = pygame.Rect(0, 0, width, height)
    rect.center = (screen_size[0] // 2, screen_size[1] // 2)

    destination = (
        getattr(route.end_node, "name", None)
        or getattr(route.end_node, "id", route.end_node)
    )
    message = f"Travel to {destination} for \u00a3{route.total_cost}?"
    player_id = player.id

    def accept():
        ev_manager.post(game_events.RouteConfirmedEvent(route.id, player_id))
        ui_manager.close_modal()

    popup = UIPopup(
        ev_manager,
        rect=rect,
        assets=assets,
        message=message,
        buttons=[
            ("Yes", accept),
            ("Cancel", ui_manager.close_modal),
        ],
    )
    ui_manager.open_modal(popup)
    ev_manager.post(game_events.RouteSelectedEvent(route.id, player_id))
    return popup

