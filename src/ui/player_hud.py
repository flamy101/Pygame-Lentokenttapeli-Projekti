"""Player HUD widgets."""

import pygame

from ui import UIElement


class PlayerHUD(UIElement):
    """Draw the current player's money in the prototype wallet panel.

    The wallet texture includes the coin swatch. The money value is read from
    ``player.money`` on every draw, so changes appear without a separate event
    or a standalone MoneyDisplay element.
    """

    def __init__(self, rect, player, assets, z_index=0, font=None, icon=None):
        super().__init__(rect, z_index)
        self.player = player
        self.assets = assets
        self.font = font if font is not None else assets.font("default")
        self.icon = icon if icon is not None else assets.image("wallet")

    @staticmethod
    def _format_money(value):
        if isinstance(value, float):
            return f"{value:g}"
        return str(value)

    def draw(self, screen: pygame.Surface):
        wallet = self.icon
        if wallet.get_size() != self.rect.size:
            wallet = pygame.transform.scale(wallet, self.rect.size)
        screen.blit(wallet, self.rect.topleft)

        text = self.font.render(self._format_money(self.player.money), True, (255, 255, 255))
        text_rect = text.get_rect(
            center=(self.rect.left + round(self.rect.width * 0.45), self.rect.centery)
        )
        screen.blit(text, text_rect)
