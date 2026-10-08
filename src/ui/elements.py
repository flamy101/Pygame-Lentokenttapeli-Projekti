import pygame
from ui import UIElement


import pygame


class Button(UIElement):
           
    """
    A clickable, hoverable rectangular UI element with optional text.
    """

    def __init__(self, rect, callback=None, z_index=0,
                 color=(70, 70, 70), hover_color=(100, 100, 100),
                 text=None, font=None, text_color=(255, 255, 255),
                 border_color=None, border_width=0, border_radius=0):
        super().__init__(rect, z_index)
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.text = text
        self.font = font
        self.text_color = text_color
        self.border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius
        self.highlighted = False

    def draw(self, screen):
        color = self.hover_color if self.highlighted else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
        if self.border_color and self.border_width:
            pygame.draw.rect(
                screen, self.border_color, self.rect, self.border_width,
                border_radius=self.border_radius,
            )

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


class DiceDisplay(UIElement):
    """A framed dice result that cycles through faces while a roll resolves."""

    BACKGROUND = (43, 38, 35)
    GOLD = (224, 180, 104)

    def __init__(self, rect, font, z_index=5):
        super().__init__(rect, z_index)
        self.font = font
        self.value = 0
        self.final_value = 0
        self.rolling = False
        self.elapsed = 0.0
        self.duration = 0.9

    @property
    def text(self):
        return str(self.final_value)

    @text.setter
    def text(self, value):
        try:
            self.final_value = int(value)
        except (TypeError, ValueError):
            self.final_value = 0
        self.elapsed = 0.0
        self.rolling = True

    def update(self, dt):
        if not self.rolling:
            return
        self.elapsed += max(0.0, dt)
        if self.elapsed >= self.duration:
            self.rolling = False
            self.value = self.final_value
        else:
            # The changing faces slow down near the end for a more deliberate stop.
            progress = self.elapsed / self.duration
            interval = 0.045 + progress * 0.11
            face = int(self.elapsed / interval) % 6 + 1
            self.value = face

    def draw(self, screen):
        shadow_rect = self.rect.move(0, 5)
        pygame.draw.rect(screen, (28, 24, 22), shadow_rect, border_radius=12)
        pygame.draw.rect(screen, self.BACKGROUND, self.rect, border_radius=12)
        pygame.draw.rect(screen, self.GOLD, self.rect, 3, border_radius=12)
        inset = self.rect.inflate(-12, -12)
        pygame.draw.rect(screen, (75, 62, 53), inset, 1, border_radius=8)

        display_value = self.value if self.rolling or self.value else self.final_value
        if self.rolling:
            pulse = (pygame.time.get_ticks() // 100) % 2
            if pulse:
                pygame.draw.rect(screen, (247, 211, 139), self.rect, 2, border_radius=12)
        number = self.font.render(str(display_value), True, (255, 244, 213))
        if self.rolling:
            progress = min(1.0, self.elapsed / self.duration)
            angle = round(7 * (1.0 - progress) * pygame.math.Vector2(1, 0).rotate(self.elapsed * 500).y)
            number = pygame.transform.rotate(number, angle)
        screen.blit(number, number.get_rect(center=self.rect.center))


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

    def bind(self, player):
        """Bind the badge to the player selected by its owning scene."""
        self.current_player = player

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
    





