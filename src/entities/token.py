"""Visual and gameplay data for a token placed on a map node."""

import pygame


class Token:
    """A passive node token; arrival handling belongs to Player/TurnManager."""

    def __init__(
        self,
        id,
        token_type: str,
        category: str,
        money_delta: int,
        texture: pygame.Surface,
    ):
        self.id = id
        self.token_type = token_type
        self.category = category
        self.money_delta = money_delta
        self.texture = texture
        self.is_claimed = False

    def draw(self, screen: pygame.Surface, pos: tuple[int, int]):
        """Blit the token centered at its node's screen position."""
        screen.blit(self.texture, self.texture.get_rect(center=pos))
