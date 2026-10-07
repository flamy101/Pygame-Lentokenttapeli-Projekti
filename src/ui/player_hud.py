"""Player HUD widgets."""

import pygame

from ui import UIElement


class PlayerHUD(UIElement):
    """Draw a bound player's wallet, inventory card, and color badge.

    The wallet texture includes the coin swatch. The money value is read from
    ``player.money`` on every draw, so changes appear without a separate event
    or a standalone MoneyDisplay element. The owner of this HUD is responsible
    for calling ``bind`` when the active player changes.
    """

    def __init__(
        self,
        ev_manager=None,
        player=None,
        rect=None,
        assets=None,
        z_index=0,
        font=None,
        icon=None,
        inventory_rect=None,
    ):
        # Keep accepting the previous PlayerHUD(rect, player, assets) form.
        if isinstance(ev_manager, pygame.Rect):
            old_rect, old_player, old_assets = ev_manager, player, rect
            ev_manager, player, rect, assets = None, old_player, old_rect, old_assets
        if player is None or rect is None or assets is None:
            raise TypeError("PlayerHUD requires a player, rect, and assets")

        super().__init__(rect, z_index)
        self.player = player
        self.assets = assets
        self.ev_manager = ev_manager
        self.font = font if font is not None else assets.font("default")
        self.small_font = font if font is not None else assets.font("default")
        self.icon = icon if icon is not None else assets.image("wallet")
        if inventory_rect is None:
            inventory_width = max(140, rect.width)
            inventory_height = 260
            inventory_rect = pygame.Rect(
                rect.right - inventory_width,
                rect.top - inventory_height - 12,
                inventory_width,
                inventory_height,
            )
        self.inventory_rect = pygame.Rect(inventory_rect)

    def bind(self, player):
        """Change which player's live state this panel displays."""
        self.player = player

    @staticmethod
    def _format_money(value):
        if isinstance(value, float):
            return f"{value:g}"
        return str(value)

    def draw(self, screen: pygame.Surface):
        self._draw_inventory(screen)

        wallet = self.icon
        if wallet.get_size() != self.rect.size:
            wallet = pygame.transform.scale(wallet, self.rect.size)
        screen.blit(wallet, self.rect.topleft)

        text = self.font.render(self._format_money(self.player.money), True, (255, 255, 255))
        text_rect = text.get_rect(
            center=(self.rect.left + round(self.rect.width * 0.45), self.rect.centery)
        )
        screen.blit(text, text_rect)

    @staticmethod
    def _item_rows(items):
        """Return (icon key, quantity) pairs for common Player.items shapes."""
        if items is None:
            return []
        if isinstance(items, dict):
            entries = items.items()
        else:
            entries = ((item, item) for item in items)

        rows = []
        for key, value in entries:
            if isinstance(value, (int, float)):
                icon_key, quantity = key, value
            else:
                if isinstance(value, dict):
                    get = value.get
                else:
                    get = lambda name, default=None: getattr(value, name, default)
                icon_key = (
                    get("icon")
                    or get("image")
                    or get("token_type")
                    or get("name")
                    or key
                )
                quantity = get("quantity", get("count", 1))
            if quantity and quantity > 0:
                rows.append((icon_key, quantity))
        return rows

    def _resolve_item_icon(self, key):
        if isinstance(key, pygame.Surface):
            return key
        if key is None:
            return None
        image = getattr(self.assets, "images", {}).get(str(key))
        if image is not None:
            return image
        try:
            return self.assets.image(str(key))
        except (KeyError, RuntimeError):
            return None

    def _draw_inventory(self, screen):
        panel = self.inventory_rect
        pygame.draw.rect(screen, (65, 45, 50), panel)
        pygame.draw.rect(screen, (220, 170, 95), panel, 3)

        badge_radius = max(5, min(12, (panel.height - 24) // 2))
        badge_center = (panel.right - 18, panel.top + 18)
        player_color = getattr(self.player, "color", (180, 180, 180))
        pygame.draw.circle(screen, player_color, badge_center, badge_radius)
        pygame.draw.circle(screen, (30, 30, 30), badge_center, badge_radius, 1)

        rows = self._item_rows(getattr(self.player, "items", None))
        if not rows:
            return

        padding = 8
        columns = max(1, (panel.width - padding * 2) // 44)
        cell_size = min(44, (panel.width - padding * 2) // columns)
        icon_size = max(12, cell_size - 10)
        for index, (icon_key, quantity) in enumerate(rows):
            col, row = index % columns, index // columns
            left = panel.left + padding + col * cell_size
            top = panel.top + 36 + row * cell_size
            if top + cell_size > panel.bottom - padding:
                break

            icon = self._resolve_item_icon(icon_key)
            if icon is not None:
                icon = pygame.transform.smoothscale(icon, (icon_size, icon_size))
                icon_rect = icon.get_rect(
                    center=(left + cell_size // 2, top + cell_size // 2)
                )
                screen.blit(icon, icon_rect)
            else:
                fallback = pygame.Rect(left + 5, top + 5, icon_size, icon_size)
                pygame.draw.rect(screen, (145, 105, 75), fallback, border_radius=4)
                label = str(icon_key)[:1].upper() if icon_key is not None else "?"
                glyph = self.small_font.render(label, True, (255, 245, 225))
                screen.blit(glyph, glyph.get_rect(center=fallback.center))

            count = self.small_font.render(str(quantity), True, (255, 255, 255))
            count_rect = count.get_rect(bottomright=(left + cell_size - 1, top + cell_size - 1))
            badge = count_rect.inflate(6, 2)
            pygame.draw.rect(screen, (40, 30, 30), badge, border_radius=4)
            screen.blit(count, count_rect)
