from __future__ import annotations

import events


class UIManager:

    def __init__(self, ev_manager):

        self.ev_manager = ev_manager
        ev_manager.register_listener(self)

        self.elements: list[UIElement] = []
        self.hovered: UIElement | None = None
        self.focused: UIElement | None = None
        self.modal: UIElement | None = None

    def add(self, element):
        """
        :param element: to add
        Adds an element to UIManager elements
        """

        self.elements.append(element)
        self.elements.sort(key=lambda e: e.z_index, reverse=True)

    def remove(self, element):
        """
        :param element: to remove
        Removes an element from UIManager elements
        """

        self.elements.remove(element)

        if self.hovered is element:
            self.hovered = None

        if self.focused is element:
            self.focused = None

    def _topmost_at(self,pos):
        if self.modal is not None:
            for button in self.modal.child_buttons:
                if button.rect.collidepoint(pos):
                    return button
            return None

        for element in self.elements:
            if element.rect.collidepoint(pos):
                return element
        return None

    def open_modal(self, popup: UIElement):
        if self.hovered is not None:
            self.hovered.on_hover_end()
        self.hovered = None
        self.focused = None
        self.modal = popup

    def close_modal(self):
        if self.modal is None:
            return
        child_buttons = self.modal.child_buttons
        if self.hovered in child_buttons:
            self.hovered.on_hover_end()
        if self.focused in child_buttons:
            self.focused = None
        self.hovered = None
        self.modal = None

    def draw_modal(self, screen):
        if self.modal is not None:
            self.modal.draw(screen)

    def notify(self, event):
        match event:
            case events.MouseMoveEvent(pos):
                hit = self._topmost_at(pos)

                if hit is not self.hovered:
                    if self.hovered:
                        self.hovered.on_hover_end()
                    if hit:
                        hit.on_hover_start()

                    self.hovered = hit

            case events.MouseInputEvent(pos):
                hit = self._topmost_at(pos)
                if hit:
                    self.focused = hit
                    hit.on_click()

            case events.KeyInputEvent(key) if self.focused:
                self.focused.on_key(key)


class UIElement:

    def __init__(self, rect, z_index=0):
        self.rect = rect
        self.z_index = z_index
        self.highlighted = False

    def draw(self, screen): pass
    def on_click(self): pass
    def on_hover_start(self): pass
    def on_hover_end(self): pass
    def on_key(self, key): pass
