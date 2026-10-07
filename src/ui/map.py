import pygame

import events
import game_events
from ui import UIElement


class Map(UIElement):

    def __init__(self, rect, z_index, ev_manager, color, container, texture, ui_manager=None):
        """
        :param container: pygame.Rect — the visible viewport the map must always fully cover.
        """
        super().__init__(rect, z_index)
        self.ev_manager = ev_manager
        self.ui_manager = ui_manager
        ev_manager.register_listener(self)

        self.color = color
        self.container = container

        self.original_x = float(rect.x)
        self.original_y = float(rect.y)
        self.x = float(rect.x)
        self.y = float(rect.y)
        self.w = float(rect.w)
        self.h = float(rect.h)

        self.map_surface = rect
        self.texture = texture
        self._scaled_texture = None
        self._scaled_size = None

        self.min_zoom_w = container.w
        self.min_zoom_h = container.h

    def notify(self, event):
        if self.ui_manager is not None and self.ui_manager.modal is not None:
            return

        match event:
            case game_events.MapMoveEvent():
                self.x += event.dx
                self.y += event.dy
                self._apply()

            case events.MouseScrollEvent():
                factor = (event.scroll_y + 10) / 10
                self._zoom(factor, event.pos)

            case game_events.MapScaleEvent():
                factor = event.zoom
                self._zoom(factor, [0,0])



    def _zoom(self, factor, anchor):
        """
        Scale the map by factor, zooming is centered under the cursor.
        """
        new_w = max(self.w * factor, self.min_zoom_w)
        new_h = max(self.h * factor, self.min_zoom_h)

        # Keep the point under the cursor in the same place after resizing.
        rel_x = (anchor[0] - self.x) / self.w
        rel_y = (anchor[1] - self.y) / self.h

        self.x = anchor[0] - rel_x * new_w
        self.y = anchor[1] - rel_y * new_h
        self.w = new_w
        self.h = new_h

        self._apply()

    def _apply(self):
        """
        Write the float state into map_surface, then clamp to container
        """
        self.map_surface.x = round(self.x)
        self.map_surface.y = round(self.y)
        self.map_surface.w = round(self.w)
        self.map_surface.h = round(self.h)

        self._clamp_to_container()

        self.x = self.map_surface.x
        self.y = self.map_surface.y

    def _clamp_to_container(self):
        rect, container = self.map_surface, self.container

        if rect.width <= container.width:
            rect.centerx = container.centerx
        else:
            if rect.left > container.left:
                rect.left = container.left
            if rect.right < container.right:
                rect.right = container.right

        if rect.height <= container.height:
            rect.centery = container.centery
        else:
            if rect.top > container.top:
                rect.top = container.top
            if rect.bottom < container.bottom:
                rect.bottom = container.bottom

    def draw(self, screen):
        previous_clip = screen.get_clip()
        screen.set_clip(self.container)

        current_size = self.map_surface.size
        if current_size != self._scaled_size:
            self._scaled_texture = pygame.transform.scale(
                self.texture, current_size
            )
            self._scaled_size = current_size

        screen.blit(self._scaled_texture, self.map_surface.topleft)

        screen.set_clip(previous_clip)
