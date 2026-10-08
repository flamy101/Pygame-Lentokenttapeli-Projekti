"""Modal message popup with a row of callback buttons."""

from collections.abc import Callable

import pygame

from ui import UIElement
from ui.elements import Button


class UIPopup(UIElement):
    """Dim the screen and show a bordered message with action buttons."""

    def __init__(
        self,
        ev_manager,
        rect: pygame.Rect,
        assets,
        message: str,
        buttons: list[tuple[str, Callable]],
        z_index: int = 10_000,
        image: pygame.Surface | None = None,
    ):
        super().__init__(rect, z_index)
        self.ev_manager = ev_manager
        self.assets = assets
        self.message = message
        self.image = image
        self.font = assets.font("default")
        self.button_font = assets.fonts.get("small", self.font)
        self.child_buttons: list[Button] = []

        count = len(buttons)
        if count:
            padding = 16
            gap = 10
            button_height = min(42, max(28, rect.height // 4))
            available_width = max(1, rect.width - padding * 2 - gap * (count - 1))
            button_width = max(1, available_width // count)
            row_width = count * button_width + (count - 1) * gap
            left = rect.centerx - row_width // 2
            top = rect.bottom - padding - button_height

            for index, (label, callback) in enumerate(buttons):
                button_rect = pygame.Rect(
                    left + index * (button_width + gap),
                    top,
                    button_width,
                    button_height,
                )
                self.child_buttons.append(
                    Button(
                        button_rect,
                        callback=callback,
                        z_index=z_index + 1,
                        text=label,
                        font=self.button_font,
                        color=(105, 65, 55),
                        hover_color=(145, 90, 65),
                    )
                )

    def _wrapped_lines(self, max_width: int) -> list[str]:
        lines = []
        line = ""
        for word in self.message.split():
            candidate = f"{line} {word}".strip()
            if line and self.font.size(candidate)[0] > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        return lines

    def draw(self, screen: pygame.Surface):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (65, 45, 50), self.rect, border_radius=10)
        pygame.draw.rect(screen, (220, 170, 95), self.rect, 3, border_radius=10)

        button_top = min(
            (button.rect.top for button in self.child_buttons),
            default=self.rect.bottom - 12,
        )
        text_area_height = max(0, button_top - self.rect.top - 24)
        image_height = 0
        if self.image is not None:
            image = self.image
            image_width, source_height = image.get_size()
            scale = min(1.0, 96 / max(1, image_width), 96 / max(1, source_height))
            image = pygame.transform.smoothscale(
                image, (max(1, round(image_width * scale)), max(1, round(source_height * scale)))
            )
            image_rect = image.get_rect(midtop=(self.rect.centerx, self.rect.top + 12))
            screen.blit(image, image_rect)
            image_height = image_rect.height + 8
        lines = self._wrapped_lines(max(1, self.rect.width - 32))
        line_height = self.font.get_linesize()
        total_text_height = len(lines) * line_height
        y = self.rect.top + 12 + image_height + max(0, (text_area_height - image_height - total_text_height) // 2)

        for line in lines:
            rendered = self.font.render(line, True, (255, 245, 225))
            screen.blit(rendered, rendered.get_rect(midtop=(self.rect.centerx, y)))
            y += line_height

        for button in self.child_buttons:
            button.draw(screen)
