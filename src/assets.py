import os.path
import pygame
import events as ev


class Assets:
    """
    Central store for loaded pygame resources (fonts, images, sounds).

    Populated once, in response to PygameReadyEvent, after pygame.font.init()
    and the display have been set up.
    """

    ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

    def __init__(self, ev_manager):
        self.ev_manager = ev_manager
        ev_manager.register_listener(self)

        self.fonts: dict[str, pygame.font.Font] = {}
        self.images: dict[str, pygame.Surface] = {}
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.music_tracks: dict[str, str] = {}
        self.is_loaded = False

    def notify(self, event):
        if isinstance(event, ev.PygameReadyEvent):
            self.load()
            self.ev_manager.post(ev.AssetsReadyEvent())

    def load(self):
        """
        Load every shared resource once. Safe to call only after
        pygame.font.init() has run.
        """
        pixel_font_path = os.path.join(
            self.ASSET_DIR, "aseprite-src-files", "PressStart2P-Regular.ttf"
        )
        self.fonts["default"] = pygame.font.Font(pixel_font_path, 20)
        self.fonts["heading"] = pygame.font.Font(pixel_font_path, 36)
        self.fonts["small"] = pygame.font.SysFont("Arial", 14)
        self.fonts["airport"] = pygame.font.Font(pixel_font_path, 21)
        self.fonts["dice"] = pygame.font.Font(pixel_font_path, 44)

        self.images["map"] = pygame.image.load(
            os.path.join(self.ASSET_DIR, "map-264.png")
        ).convert_alpha()
        self.images["menu-bkg-img"] = pygame.image.load(
            os.path.join(self.ASSET_DIR, "menu_background.png")
        )
        self.images["wallet"] = pygame.image.load(
            os.path.join(self.ASSET_DIR, "wallet.png")
        ).convert_alpha()

        # Board entities & map sprites
        general_textures = {
            "token-backside": "token-backside.png",
            "token-deck": "token-deck.png",
            "node": "node.png",
            "player-blue": "player-blue.png",
            "player-red": "player-red.png",
            "route-arrow": "route-arrow.png",
        }
        for key, filename in general_textures.items():
            path = os.path.join(self.ASSET_DIR, filename)
            if os.path.isfile(path):
                self.images[key] = pygame.image.load(path).convert_alpha()

        token_textures = {
            "merkki-varoitus-lv1": "merkki-varoitus-lv1.png",
            "merkki-200-iq-lv2": "merkki-200-iq-lv2.png",
            "merkki-bitcoin-lvl3": "merkki-bitcoin-lvl3.png",
            "merkki-special-bandit": "merkki-special-bandit.png",
            "merkki-special-horseshoe": "merkki-special-horseshoe.png",
        }
        for key, filename in token_textures.items():
            path = os.path.join(self.ASSET_DIR, filename)
            if os.path.isfile(path):
                self.images[key] = pygame.image.load(path).convert_alpha()

        empty_token = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(empty_token, (232, 224, 195), (16, 16), 15)
        pygame.draw.circle(empty_token, (95, 85, 70), (16, 16), 15, 2)
        self.images["token-empty"] = empty_token

        aliases = {
            "warning": "merkki-varoitus-lv1",
            "200_iq": "merkki-200-iq-lv2",
            "bitcoin": "merkki-bitcoin-lvl3",
            "bandit": "merkki-special-bandit",
            "horseshoe": "merkki-special-horseshoe",
        }
        for alias, target_key in aliases.items():
            if target_key in self.images:
                self.images[alias] = self.images[target_key]

        self.load_music("menu-ost", "music_OST.mp3")

        self.is_loaded = True

    def font(self, name: str) -> pygame.font.Font:
        if not self.is_loaded:
            raise RuntimeError("Assets.font() called before InitializeEvent was handled")
        try:
            return self.fonts[name]
        except KeyError:
            raise KeyError(
                f"No font registered under '{name}'. Available: {list(self.fonts)}"
            ) from None

    def image(self, name: str) -> pygame.Surface:
        if not self.is_loaded:
            raise RuntimeError("Assets.image() called before load()")
        try:
            return self.images[name]
        except KeyError:
            raise KeyError(
                f"No image registered under '{name}'. Available: {list(self.images)}"
            ) from None

    def load_music(self, name: str, filename: str) -> str | None:
        path = os.path.join(self.ASSET_DIR, filename)
        if not os.path.isfile(path):
            print(f"Warning: music file for '{name}' not found at {path}")
            return None
        self.music_tracks[name] = path
        return path

    def music_path(self, name: str) -> str | None:
        if not self.is_loaded:
            raise RuntimeError("Assets.music_path() called before load()")
        return self.music_tracks.get(name)
