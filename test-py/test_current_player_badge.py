import pygame

from ui.elements import CurrentPlayerBadge


class Player:
    def __init__(self, player_id, name, color, turn_order):
        self.id = player_id
        self.name = name
        self.color = color
        self.turn_order = turn_order


class EventManager:
    def __init__(self):
        self.listeners = []

    def register_listener(self, listener):
        self.listeners.append(listener)

    def post(self, event):
        for listener in self.listeners:
            listener.notify(event)


class Assets:
    def font(self, name):
        assert name == "default"
        return pygame.font.SysFont("Arial", 16)


def test_badge_can_be_bound_and_draws_the_selected_player():
    pygame.init()
    try:
        first = Player(1, "First", (200, 20, 30), 1)
        second = Player(2, "Second", (20, 40, 210), 2)
        manager = EventManager()
        badge = CurrentPlayerBadge(
            manager,
            pygame.Rect(10, 10, 240, 48),
            Assets(),
            {second.id: second, first.id: first},
            z_index=4,
        )
        screen = pygame.Surface((280, 80))

        assert badge.current_player is first
        badge.draw(screen)
        assert screen.get_at((20, 34))[:3] == first.color

        badge.bind(second)
        assert badge.current_player is second
        badge.draw(screen)
        assert screen.get_at((20, 34))[:3] == second.color
    finally:
        pygame.quit()
