import pygame


class Node:
    """
    Represents a map node (City, Capital, or Waypoint).
    Purely visual and spatial; does not listen to Pygame events.
    """

    def __init__(
        self,
        node_id: str,
        lat: float,
        lon: float,
        projector,
        name: str = None,  # ty: ignore[invalid-parameter-default]
        is_capital: bool = False,
        is_waypoint: bool = False,
        region: str = "default",
        radius: int = 4,
        color: tuple = (255, 255, 255),
        font: pygame.font.Font = None,  # ty: ignore[invalid-parameter-default]
    ):

        self.id = node_id
        self.name = name
        self.lat = lat
        self.lon = lon

        self.is_capital = is_capital
        self.is_waypoint = is_waypoint
        self.region = region

        self.radius = radius
        self.color = color
        self.font = font

        self.pos_x, self.pos_y = projector(lat, lon)

        self.highlighted = False

        self.text_surface = None
        self.text_rect = None
        if not self.is_waypoint and self.name and self.font:
            shadow_surf = self.font.render(self.name, True, (0, 0, 0))
            self.text_surface = self.font.render(self.name, True, (255, 255, 255))

            base_x = self.pos_x + self.radius + 5
            base_y = self.pos_y

            self.shadow_rect = shadow_surf.get_rect(midleft=(base_x + 1, base_y + 1))
            self.text_rect = self.text_surface.get_rect(midleft=(base_x, base_y))
            self._shadow_surf = shadow_surf

    def draw(self, surface: pygame.Surface):
        """Draws the node and its label based on its type and state."""

        if self.highlighted:
            highlight_radius = self.radius + 5
            pygame.draw.circle(
                surface, (255, 215, 0), (self.pos_x, self.pos_y), highlight_radius, 2
            )

        if self.is_waypoint:
            pygame.draw.circle(
                surface, self.color, (self.pos_x, self.pos_y), self.radius
            )
        else:
            draw_radius = self.radius + 2 if self.is_capital else self.radius
            pygame.draw.circle(
                surface, self.color, (self.pos_x, self.pos_y), draw_radius
            )

            if self.is_capital:
                pygame.draw.circle(
                    surface, (0, 0, 0), (self.pos_x, self.pos_y), draw_radius - 2
                )

        if self.text_surface:
            surface.blit(self._shadow_surf, self.shadow_rect)
            surface.blit(self.text_surface, self.text_rect)  # ty: ignore[invalid-argument-type]

    def hit_test(self, mouse_pos: tuple[int, int]) -> bool:
        """
        Checks if the mouse position intersects with the node.
        Returns False immediately for waypoints (they cannot be clicked).
        """
        if self.is_waypoint:
            return False

        dx = self.pos_x - mouse_pos[0]
        dy = self.pos_y - mouse_pos[1]
        distance_sq = dx * dx + dy * dy

        click_radius = self.radius + 4
        return distance_sq <= (click_radius * click_radius)

    def set_highlighted(self, state: bool):
        """Allows external systems (like RouteArrow) to flag this node."""
        self.highlighted = state
