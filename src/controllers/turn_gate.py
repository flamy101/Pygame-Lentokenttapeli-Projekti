"""Hot-seat player handoff using the reusable UIPopup modal."""

import pygame

import game_events
from ui.popup import UIPopup


class TurnGate:
    """Open a pass-device confirmation popup when a turn changes."""

    def __init__(self, ev_manager, ui_manager, assets, players: dict[int, object]):
        self.ev_manager = ev_manager
        self.ui_manager = ui_manager
        self.assets = assets
        self.players = players
        ev_manager.register_listener(self)

    def _lookup_player(self, player_id):
        if player_id in self.players:
            return self.players[player_id]
        for player in self.players.values():
            if player.id == player_id:
                return player
        raise KeyError(f"No player found for turn id {player_id!r}")

    @staticmethod
    def _popup_rect():
        screen = pygame.display.get_surface()
        screen_size = screen.get_size() if screen is not None else (1200, 900)
        rect = pygame.Rect(0, 0, min(480, screen_size[0] - 24), min(220, screen_size[1] - 24))
        rect.center = (screen_size[0] // 2, screen_size[1] // 2)
        return rect

    def notify(self, event):
        if not isinstance(event, game_events.TurnEndedEvent):
            return

        player = self._lookup_player(event.next_player_id)
        player_id = event.next_player_id
        popup = UIPopup(
            self.ev_manager,
            rect=self._popup_rect(),
            assets=self.assets,
            message=f"Player {player.name}'s turn — pass the device",
            buttons=[("Ready", lambda: self._confirm_ready(player_id))],
            z_index=10_000,
        )
        self.ui_manager.open_modal(popup)

    def _confirm_ready(self, player_id):
        self.ev_manager.post(game_events.TurnInputReadyEvent(player_id))
        self.ui_manager.close_modal()

