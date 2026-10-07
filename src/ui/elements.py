import pygame
import game_events
import events
from ui import UIElement


import pygame


class Button(UIElement):
           
    """
    A clickable, hoverable rectangular UI element with optional text.
    """

    def __init__(self, rect, callback=None, z_index=0,
                 color=(70, 70, 70), hover_color=(100, 100, 100),
                 text=None, font=None, text_color=(255, 255, 255)):
        super().__init__(rect, z_index)
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.text = text
        self.font = font
        self.text_color = text_color
        self.highlighted = False

    def draw(self, screen):
        color = self.hover_color if self.highlighted else self.color
        pygame.draw.rect(screen, color, self.rect)

        if self.text and self.font:
            words = self.font.render(self.text, True, self.text_color)
            text_rect = words.get_rect(center=self.rect.center)
            screen.blit(words, text_rect)

    def on_hover_start(self):
        self.highlighted = True

    def on_hover_end(self):
        self.highlighted = False

    def on_click(self):
        if self.callback is not None:
            self.callback()

class Text(UIElement):

    """
    Defines the text inside Button
    """
    def __init__ (self, rect, z_index=0, fontname = None, fontsize = 40, fontcolor = (255,255,255), hover_color=(100,100,100),text = None ):
        super(). __init__(rect, z_index)
        self.fontname = fontname
        self.fontsize = fontsize 
        self.fontcolor = fontcolor
        self.hover_color = hover_color
        self.text = text
        self.highlighted = False

    def draw(self, screen):
        font = pygame.font.Font(self.fontname, self.fontsize)
        color = self.hover_color if self.highlighted else self.fontcolor
        words = font.render(self.text, True, color)

        text_rect = words.get_rect(center=self.rect.center)
        screen.blit(words, text_rect)

    def on_hover_start(self):
        self.highlighted = True

    def on_hover_end(self):
        self.highlighted = False


class CurrentPlayerBadge(UIElement):
    """Displays the active player's name and color swatch."""

    def __init__(self, ev_manager, rect, assets, players: dict[int, object], z_index=0):
        super().__init__(rect, z_index)
        self.ev_manager = ev_manager
        self.assets = assets
        self.players = players
        self.current_player = min(
            players.values(),
            key=lambda player: player.turn_order,
            default=None,
        )
        ev_manager.register_listener(self)

    def notify(self, event):
        if isinstance(event, game_events.TurnEndedEvent):
            self._bind_player(event.next_player_id)

    def _bind_player(self, player_id):
        if player_id in self.players:
            self.current_player = self.players[player_id]
            return

        # Support lookups keyed by database IDs of a different scalar type.
        for player in self.players.values():
            if player.id == player_id:
                self.current_player = player
                return

        raise KeyError(f"No player found for turn id {player_id!r}")

    def draw(self, screen):
        player = self.current_player
        if player is None:
            return

        padding = 8
        swatch_size = max(1, min(28, self.rect.height - 2 * padding))
        swatch_rect = pygame.Rect(
            self.rect.left + padding,
            self.rect.centery - swatch_size // 2,
            swatch_size,
            swatch_size,
        )
        pygame.draw.rect(screen, player.color, swatch_rect)
        pygame.draw.rect(screen, (30, 30, 30), swatch_rect, 1)

        font = self.assets.font("default")
        label = font.render(player.name, True, (255, 255, 255))
        label_rect = label.get_rect(
            midleft=(swatch_rect.right + padding, self.rect.centery)
        )
        screen.blit(label, label_rect)
    





