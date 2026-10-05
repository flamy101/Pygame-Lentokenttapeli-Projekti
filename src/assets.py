import os.path

import pygame

import events as ev


class Assets:
    """
    Central store for loaded pygame resources (fonts, images, sounds).

    Populated once, in response to InitializeEvent, after pygame.font.init()
    and the display have been set up. Scenes and UI elements read from this
    rather than creating their own resources.
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
        self.fonts["default"] = pygame.font.SysFont("Arial", 20)
        self.fonts["heading"] = pygame.font.SysFont("Arial", 36, bold=True)
        self.fonts["small"] = pygame.font.SysFont("Arial", 14)

        self.images["map"] = pygame.image.load(
            os.path.join(self.ASSET_DIR, "map-264.png")
        ).convert_alpha()
        self.images["menu-bkg-img"] = pygame.image.load(
            os.path.join(self.ASSET_DIR, "menu_background.png")
        )

        self.load_music("menu-ost", "music_OST.mp3")

        self.is_loaded = True

    def font(self, name: str) -> pygame.font.Font:
        """
        Look up a loaded font by name, with a clear error if it's missing
        or requested too early.
        """
        if not self.is_loaded:
            raise RuntimeError("Assets.font() called before InitializeEvent was handled")
        try:
            return self.fonts[name]
        except KeyError:
            raise KeyError(f"No font registered under '{name}'. "
                            f"Available: {list(self.fonts)}") from None

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
        """
        Register a music file under `name`. Music is streamed from disk by
        pygame.mixer.music, so only the path is stored here.
        """
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


