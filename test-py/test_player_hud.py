import pygame

from ui.player_hud import PlayerHUD


class Player:
    money = 275


class RecordingFont:
    def __init__(self):
        self.font = pygame.font.SysFont("Arial", 20)
        self.rendered = []

    def render(self, text, antialias, color):
        self.rendered.append(text)
        return self.font.render(text, antialias, color)


class Assets:
    def __init__(self):
        self.wallet = pygame.Surface((110, 70), pygame.SRCALPHA)
        self.wallet.fill((90, 45, 40, 255))
        self.font_instance = RecordingFont()

    def font(self, name):
        assert name == "default"
        return self.font_instance

    def image(self, name):
        assert name == "wallet"
        return self.wallet


def test_player_hud_draws_wallet_and_reads_money_each_frame():
    pygame.init()
    try:
        assets = Assets()
        player = Player()
        hud = PlayerHUD(pygame.Rect(5, 5, 110, 70), player, assets)
        screen = pygame.Surface((130, 90), pygame.SRCALPHA)

        hud.draw(screen)
        assert assets.font_instance.rendered[-1] == "275"
        assert screen.get_at((6, 6))[:3] == (90, 45, 40)

        player.money = 300
        hud.draw(screen)
        assert assets.font_instance.rendered[-1] == "300"
    finally:
        pygame.quit()
