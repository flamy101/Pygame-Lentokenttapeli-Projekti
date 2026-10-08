import pygame

import events


class Graphics:
    """
    Draws the model state onto the screen
    """

    def __init__(self, ev_manager, model, scene_manager):
        """

        :param ev_manager:  Allows posting messages to the event queue.
        :param model: a strong reference to the game Model.

        is_initialized (bool): pygame is ready to draw.
        screen (pygame.Surface): pygame screen object.
        clock (pygame.time.Clock): keeps the fps constant.

        """

        self.ev_manager = ev_manager
        ev_manager.register_listener(self)
        self.model = model
        self.is_initialized = False
        self.screen = None
        self.vsync_fps = 0
        self.scene_manager = scene_manager

    def  notify(self, event):
        """
        Recieves events from the event queue.

        :param self:
        :param event:
        :return:
        """
        match event:
            case events.InitializeEvent():
                self.initialize()

            case events.QuitEvent():
                self.is_initialized = False

            case events.TickEvent():
                if not self.is_initialized:
                    return
                self.renderall()

    def initialize(self):
        pygame.display.init()
        pygame.font.init()
        pygame.mixer.init()
        pygame.display.set_caption("Airport Game")
        self.screen = pygame.display.set_mode((1200, 900))
        self.is_initialized = True

        refresh_rate = pygame.display.get_current_refresh_rate()
        if refresh_rate == 0:
            refresh_rate = 60  # fallback

        self.ev_manager.post(events.PygameReadyEvent(refresh_rate))

    def renderall(self):
        """
        Draw the current game state on the screen.
        Not run if is_initialized == False
        """

        assert self.screen is not None
        self.screen.fill((18, 32, 32))
        if self.scene_manager.current is not None:
            self.scene_manager.current.draw(self.screen)
        pygame.display.flip()
