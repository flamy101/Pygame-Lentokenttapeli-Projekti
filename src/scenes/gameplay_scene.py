from entities.map_node import Node
from entities.player import Player
from controllers.map_projector import MapProjector
import pygame
import random
import game_events
from controllers.dice_roller import DiceRoller
from controllers.map_controller import MapController
from scenes import Scene
from ui.elements import Button, CurrentPlayerBadge, Text
from ui.map import Map
from ui.player_hud import PlayerHUD


class GameScene(Scene):
    def __init__(self, ev_manager, ui_manager, assets, players=None):
        super().__init__(ev_manager, ui_manager, assets)
        self.ev_manager.register_listener(self)
        self.dice_roller = DiceRoller(ev_manager, rng=random.Random())
        self.temporary_player_id = "p1"
        self.players = players if players is not None else {}
        self.player_hud = None
        self.current_player_badge = None
        self.map_controller = None
        self.dice_result = 0
        self.dice_button = None
        self.dice_text = None
        self.exit_button = None
        self.game_map = None
        self.map_surface = None
        self.map_projector = None
        self.map_container = None
        self.nodes = []

    def roll_dice(self):
        self.ev_manager.post(
            game_events.RollRequestedEvent(self.temporary_player_id)
        )

    def notify(self, event):
        if isinstance(event, game_events.TurnEndedEvent):
            player = self._lookup_player(event.next_player_id)
            self.temporary_player_id = player.id
            if self.player_hud is not None:
                self.player_hud.bind(player)
            if self.current_player_badge is not None:
                self.current_player_badge.bind(player)
            return

        if isinstance(event, game_events.DiceRolledEvent):
            if event.player_id != self.temporary_player_id:
                return
            self.dice_result = event.value
            if self.dice_text is not None:
                self.dice_text.text = str(event.value)

    def _lookup_player(self, player_id):
        if player_id in self.players:
            return self.players[player_id]
        for player in self.players.values():
            if player.id == player_id:
                return player
        raise KeyError(f"No player found for turn id {player_id!r}")

    def _create_demo_player(self):
        if self.players:
            return
        node = self.nodes[0]
        player = Player(
            id=self.temporary_player_id,
            game_id="demo",
            name="Player 1",
            color=(200, 35, 45),
            money=300,
            current_node=node,
            current_route=None,
            route_progress=0,
            turn_order=0,
            is_eliminated=False,
            has_won=False,
            token_radius=8,
            ev_manager=self.ev_manager,
        )
        self.players[player.id] = player

    def _create_player_hud(self):
        if self.player_hud is not None or not self.players:
            return

        player = min(self.players.values(), key=lambda item: item.turn_order)
        self.temporary_player_id = player.id

        screen = pygame.display.get_surface()
        screen_width, screen_height = screen.get_size() if screen else (1200, 900)
        margin = 20
        column_left = max(round(screen_width * 0.75), self.map_container.right + margin)
        column_width = max(140, screen_width - column_left - margin)
        panel_height = max(180, min(510, screen_height - 390))
        inventory_rect = pygame.Rect(
            column_left, margin, column_width, panel_height
        )
        badge_rect = pygame.Rect(
            column_left + 12, margin + 8, max(1, column_width - 24), 48
        )
        wallet_width = max(1, min(220, column_width - 24))
        wallet_rect = pygame.Rect(
            column_left + (column_width - wallet_width) // 2,
            screen_height - 130,
            wallet_width,
            70,
        )

        self.player_hud = PlayerHUD(
            ev_manager=self.ev_manager,
            player=player,
            rect=wallet_rect,
            assets=self.assets,
            z_index=4,
            inventory_rect=inventory_rect,
        )
        self.current_player_badge = CurrentPlayerBadge(
            self.ev_manager,
            badge_rect,
            self.assets,
            self.players,
            z_index=5,
        )
        self.elements.extend((self.player_hud, self.current_player_badge))

    def enter(self):
        screen = pygame.display.get_surface()
        screen_width, screen_height = screen.get_size() if screen else (1200, 900)
        column_left = round(screen_width * 0.75)
        inventory_height = max(180, min(510, screen_height - 390))
        controls_y = 20 + inventory_height + 20

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
            # The roll controls sit between the inventory card and wallet.
            self.dice_button = Button(
                pygame.Rect(column_left, controls_y + 70, 200, 60),
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
                pygame.Rect(column_left, controls_y, 200, 50),
                fontsize=30,
                fontcolor=(255, 255, 255),
                text ="0"
            )
            self.elements.append(self.dice_text)

        if self.map_controller is None:
            self.map_controller = MapController(self.ev_manager, self.ui_manager)

        if self.map_surface is None:
            self.map_surface = pygame.Rect(50, 50, 800, 800)

        if self.map_container is None:
            self.map_container = pygame.Rect(50, 50, 800, 800)

        if self.map_projector is None:

            self.map_projector = MapProjector(map_bounds=(-18.00, 35.00, 38.00, 52.00), image_size=(800,800))

            node = Node(
                "1147",
                36.691002,
                3.215410,
                self.map_projector,
                is_waypoint=False,
                is_capital=False,
                radius=50,
                color=(255, 10, 10),
                font=self.assets.font("default"),
            )

            self.nodes.append(node)


        if self.game_map is None:
            self.game_map = Map(
                rect=self.map_surface,
                z_index=1,
                ev_manager=self.ev_manager,
                color=(20, 100, 0),
                container=self.map_container,
                texture=self.assets.image("map"),
                nodes=self.nodes,
                ui_manager=self.ui_manager,
            )
            self.elements.append(self.game_map)

        self._create_demo_player()
        self._create_player_hud()

        super().enter()
