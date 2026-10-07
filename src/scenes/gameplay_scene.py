import pygame
import random
import game_events
from controllers.dice_roller import DiceRoller
from controllers.map_controller import MapController
from scenes import Scene
from ui.elements import Button, Text
from ui.map import Map


class GameScene(Scene):
    def __init__(self, ev_manager, ui_manager, assets):
        super().__init__(ev_manager, ui_manager, assets)
        self.ev_manager.register_listener(self)
        self.dice_roller = DiceRoller(ev_manager, rng=random.Random())
        self.temporary_player_id = "p1"
        self.map_controller = None
        self.dice_result = 0
        self.dice_button = None
        self.dice_text = None
        self.exit_button = None
        self.game_map = None
        self.map_surface = None
        self.map_container = None

    def roll_dice(self):
        self.ev_manager.post(
            game_events.RollRequestedEvent(self.temporary_player_id)
        )

    def notify(self, event):
        if isinstance(event, game_events.DiceRolledEvent):
            if event.player_id != self.temporary_player_id:
                return
            self.dice_result = event.value
            if self.dice_text is not None:
                self.dice_text.text = str(event.value)

    def enter(self):
        if self.exit_button is None:
            self.exit_button = Button(
                pygame.Rect(0, 0, 100, 40),
                callback=lambda: self.ev_manager.post(
                    game_events.ChangeSceneEvent("menu")
                ),
                text="Exit",
                font=self.assets.font("default"),
                z_index=10
            )
            self.elements.append(self.exit_button)

        if self.dice_button is None:
            self.dice_button = Button(
                pygame.Rect(900, 700, 200, 60),
                callback=self.roll_dice,
                text="ROLL DICE",
                font=self.assets.font("default"),
                z_index=10,
                color=(0, 100, 200),
                hover_color=(0, 150, 255)
            )
            self.elements.append(self.dice_button)

        if self.dice_text is None:
            self.dice_text = Text(
                pygame.Rect(900, 620, 200, 50),
                fontsize=30,
                fontcolor=(255, 255, 255),
                text ="0"
            )
            self.elements.append(self.dice_text)

        if self.map_controller is None:
            self.map_controller = MapController(self.ev_manager)

        if self.map_surface is None:
            self.map_surface = pygame.Rect(50, 50, 800, 800)

        if self.map_container is None:
            self.map_container = pygame.Rect(50, 50, 800, 800)

        if self.game_map is None:
            self.game_map = Map(
                rect=self.map_surface,
                z_index=1,
                ev_manager=self.ev_manager,
                color=(20, 100, 0),
                container=self.map_container,
                texture=self.assets.image("map"),
            )
            self.elements.append(self.game_map)

        super().enter()
