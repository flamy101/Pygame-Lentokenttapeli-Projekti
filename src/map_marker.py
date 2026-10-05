import math

import pygame


class Node:
    """A city or waypoint displayed on the map."""

    WAYPOINT_DRAW_RADIUS = 3
    HIGHLIGHT_PADDING = 4

    def __init__(
        self,
        id,
        name,
        lat,
        lon,
        is_capital=False,
        is_waypoint=False,
        region=None,
        radius=6,
        color=(255, 255, 255),
        font=None,
    ):
        self.id = id
        self.name = name
        self.lat = lat
        self.lon = lon

        self.is_capital = is_capital
        self.is_waypoint = is_waypoint
        self.region = region

        self.radius = radius
        self.color = color
        self.font = font

        # Projected map position
        self.pos_x = 0.0
        self.pos_y = 0.0

        # Used by RouteArrow for path preview
        self.highlighted = False

    @property
    def position(self):
        return self.pos_x, self.pos_y

    def set_projected_position(self, pos_x, pos_y):
        """Set projected map coordinates."""
        self.pos_x = float(pos_x)
        self.pos_y = float(pos_y)

    def project(self, projector):
        """Project latitude/longitude into map coordinates."""

        if hasattr(projector, "project"):
            pos_x, pos_y = projector.project(
                self.lat,
                self.lon
            )
        else:
            pos_x, pos_y = projector(
                self.lat,
                self.lon
            )

        self.set_projected_position(pos_x, pos_y)

        return self.position

    def draw(self, screen, offset=(0, 0), scale=1.0):
        """Draw city or waypoint on the Pygame screen."""

        x = offset[0] + self.pos_x * scale
        y = offset[1] + self.pos_y * scale

        position = (round(x), round(y))

        # Waypoint: small dot
        if self.is_waypoint:
            pygame.draw.circle(
                screen,
                self.color,
                position,
                max(1, round(self.WAYPOINT_DRAW_RADIUS * scale)),
            )

            if self.highlighted:
                pygame.draw.circle(
                    screen,
                    self.color,
                    position,
                    max(1, round(
                        self.WAYPOINT_DRAW_RADIUS * scale
                    )) + self.HIGHLIGHT_PADDING,
                    width=2,
                )

            return

        # City
        radius = max(1, round(self.radius * scale))

        pygame.draw.circle(
            screen,
            self.color,
            position,
            radius,
        )

        # Highlight for route preview
        if self.highlighted:
            pygame.draw.circle(
                screen,
                self.color,
                position,
                radius + self.HIGHLIGHT_PADDING,
                width=2,
            )

        # City name
        if self.name and self.font is not None:
            text_surface = self.font.render(
                self.name,
                True,
                self.color,
            )

            text_position = (
                position[0] + radius + 4,
                position[1] - text_surface.get_height() // 2,
            )

            screen.blit(
                text_surface,
                text_position,
            )

    def hit_test(self, mouse_pos, offset=(0, 0), scale=1.0):
        """Check whether a city was clicked."""

        # Waypoints are not clickable
        if self.is_waypoint:
            return False

        x = offset[0] + self.pos_x * scale
        y = offset[1] + self.pos_y * scale

        radius = self.radius * scale

        dx = mouse_pos[0] - x
        dy = mouse_pos[1] - y

        return math.hypot(dx, dy) <= radius