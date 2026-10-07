import random
import pygame

from controllers.dice_roller import DiceRoller
from controllers.map_controller import MapController
from controllers.map_projector import MapProjector
from controllers.route_finder import RouteFinder
from controllers.turn_manager import TurnManager
from entities.map_node import Node
from entities.player import Player
from entities.road import Road
import game_events
from scenes import Scene
from ui.elements import Button, CurrentPlayerBadge, Text
from ui.map import Map
from ui.player_hud import PlayerHUD


class GameScene(Scene):
    def __init__(self, ev_manager, ui_manager, assets, players=None, route_finder=None, db_connector=None):
        super().__init__(ev_manager, ui_manager, assets)
        self.ev_manager.register_listener(self)
        self.db_connector = db_connector
        self.dice_roller = DiceRoller(ev_manager, rng=random.Random())
        self.players: dict[int, Player] = players if players is not None else {}
        self.route_finder = route_finder
        self.turn_manager = None
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
        self.nodes: dict[str, Node] = {}
        self.roads: list[Road] = []
        self.map_nodes: list[Node] = []
        self.routes: dict = {}

    def _get_active_player(self):
        if self.turn_manager is not None and self.turn_manager.current_player is not None:
            return self.turn_manager.current_player
        if self.players:
            return min(self.players.values(), key=lambda item: item.turn_order)
        return None

    def roll_dice(self):
        player = self._get_active_player()
        if player is None or player.current_node is None:
            print("[DEBUG] Roll Failed: No active player or current node is None.")
            return

        print(f"[DEBUG] Rolling dice for Player {player.id} (at node {player.current_node.id})...")
        self.ev_manager.post(
            game_events.RollRequestedEvent(
                player.id,
                current_node_id=player.current_node.id,
            )
        )

    def notify(self, event):
        if isinstance(event, game_events.TurnEndedEvent):
            player = self._lookup_player(event.next_player_id)
            print(f"[DEBUG] TurnEndedEvent: Transitioning to Player {player.id} ({player.name}).")
            if self.player_hud is not None:
                self.player_hud.bind(player)
            if self.current_player_badge is not None:
                self.current_player_badge.bind(player)
            return

        if isinstance(event, game_events.DiceRolledEvent):
            current_player = self._get_active_player()
            if current_player is None or event.player_id != current_player.id:
                return
            self.dice_result = event.value
            print(f"[DEBUG] DiceRolledEvent: Player {event.player_id} rolled a {event.value}.")
            if self.dice_text is not None:
                self.dice_text.text = str(event.value)

    def _lookup_player(self, player_id):
        if player_id in self.players:
            return self.players[player_id]
        for player in self.players.values():
            if player.id == player_id:
                return player
        raise KeyError(f"No player found for turn id {player_id!r}")

    def _load_map_from_db(self, db):
        """Fetch nodes and roads from MariaDB and map them to Node objects."""
        print("[DEBUG] DB Map Loading: Fetching nodes and roads from database...")
        raw_nodes = db.get_all_nodes()
        raw_roads = db.get_all_roads()

        road_node_ids = {
            str(node_id)
            for row in raw_roads
            for node_id in (row["node_a_id"], row["node_b_id"])
        }

        self.nodes = {}
        for data in raw_nodes:
            node_id = str(data["id"])
            self.nodes[node_id] = Node(
                node_id=node_id,
                name=data.get("name"),
                lat=float(data["lat"]),
                lon=float(data["lon"]),
                projector=self.map_projector,
                is_waypoint=bool(data.get("is_waypoint", False)),
                is_capital=bool(data.get("is_capital", False)),
                radius=24 if not data.get("is_waypoint") else 13,
                color=(255, 200, 0) if data.get("is_capital") else (235, 235, 220),
                font=self.assets.font("small"),
            )

        for n_id, node in list(self.nodes.items())[:5]:
            px, py = self.map_projector(node.lat, node.lon)
            print(
                f"[DEBUG] Node {n_id} ({node.lat}, {node.lon}) -> projected px: ({px}, {py})"
            )

        self.roads = []
        for r in raw_roads:
            node_a = self.nodes.get(str(r["node_a_id"]))
            node_b = self.nodes.get(str(r["node_b_id"]))
            if node_a and node_b:
                road_type_id = int(r.get("road_type_id", 1))
                road_type = {1: "land", 2: "sea", 3: "flight"}.get(
                    road_type_id, "land"
                )
                self.roads.append(
                    Road(
                        road_id=str(r["id"]),
                        node_a=node_a,
                        node_b=node_b,
                        road_type=road_type,
                        cost=float(r.get("cost", 0)),
                    )
                )


        self.map_nodes = [
            node for node_id, node in self.nodes.items() if node_id in road_node_ids
        ]

        image_width, image_height = self.assets.image("map").get_size()
        outside = [
            node.id
            for node in self.map_nodes
            if not (0 <= node.pos_x < image_width and 0 <= node.pos_y < image_height)
        ]
        if outside:
            print(f"[WARNING] {len(outside)} road-network nodes project outside map: {outside}")

        print(
            f"[DEBUG] Map Loaded: {len(self.nodes)} DB nodes, "
            f"{len(self.map_nodes)} board nodes, {len(self.roads)} drawable roads."
        )

    def _create_demo_player(self):
        if self.players or not self.nodes:
            return
        node = list(self.nodes.values())[0]
        p1_id = 1
        player = Player(
            id=str(p1_id),
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
        self.players[p1_id] = player
        print(f"[DEBUG] Fallback Player Created: 1 Demo Player at node {node.id}.")

    def _create_two_players(self, db, game_id: int):
        """Creates 2 distinct players starting at the first available node."""
        if self.players or not self.nodes:
            return

        first_node = self.nodes.get("1178", next(iter(self.nodes.values())))
        start_node_id = int(first_node.id) if str(first_node.id).isdigit() else 1

        print(f"[DEBUG] Instantiating 2 players for Game ID {game_id} at start node {start_node_id}...")

        # Player 1 (Blue)
        p1_db_id = db.insert_player(
            game_id=game_id,
            name="Player 1",
            color="blue",
            money=300,
            current_node_id=start_node_id,
            turn_order=0,
        )
        p1 = Player(
            id=p1_db_id,
            game_id=str(game_id),
            name="Player 1",
            color=(0, 120, 255),
            money=300,
            current_node=first_node,
            current_route=None,
            route_progress=0,
            turn_order=0,
            is_eliminated=False,
            has_won=False,
            token_radius=8,
            ev_manager=self.ev_manager,
        )
        p1_sprite_loaded = False
        if hasattr(self.assets, "image"):
            p1_img = self.assets.image("player-blue")
            if p1_img is not None:
                setattr(p1, "sprite", p1_img)
                p1_sprite_loaded = True

        print(f"[DEBUG] Player Created: Player 1 (DB ID: {p1_db_id}) | Sprite Loaded: {p1_sprite_loaded}")

        # Player 2 (Red)
        p2_db_id = db.insert_player(
            game_id=game_id,
            name="Player 2",
            color="red",
            money=300,
            current_node_id=start_node_id,
            turn_order=1,
        )
        p2 = Player(
            id=p2_db_id,
            game_id=str(game_id),
            name="Player 2",
            color=(230, 40, 40),
            money=300,
            current_node=first_node,
            current_route=None,
            route_progress=0,
            turn_order=1,
            is_eliminated=False,
            has_won=False,
            token_radius=8,
            ev_manager=self.ev_manager,
        )
        p2_sprite_loaded = False
        if hasattr(self.assets, "image"):
            p2_img = self.assets.image("player-red")
            if p2_img is not None:
                setattr(p2, "sprite", p2_img)
                p2_sprite_loaded = True

        print(f"[DEBUG] Player Created: Player 2 (DB ID: {p2_db_id}) | Sprite Loaded: {p2_sprite_loaded}")

        self.players = {p1_db_id: p1, p2_db_id: p2}

    def _create_player_hud(self):
        if self.player_hud is not None or not self.players:
            print("[DEBUG] Player HUD creation skipped (already created or no players).")
            return

        player = min(self.players.values(), key=lambda item: item.turn_order)

        screen = pygame.display.get_surface()
        screen_width, screen_height = screen.get_size() if screen else (1200, 900)
        margin = 20
        map_right = self.map_container.right if self.map_container else 850
        column_left = max(round(screen_width * 0.75), map_right + margin)
        column_width = max(140, screen_width - column_left - margin)
        panel_height = max(180, min(510, screen_height - 390))

        inventory_rect = pygame.Rect(
            column_left, margin, column_width, panel_height
        )
        badge_rect = pygame.Rect(
            column_left + 12, margin + 8, max(1, column_width - 24), 48
        )
        wallet_width = max(1, min(100, column_width - 24))
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
        print(f"[DEBUG] Player HUD & Badge initialized for initial active player: {player.name} (ID: {player.id}).")

    def _create_turn_manager(self):
        if self.turn_manager is not None or not self.players:
            print("[DEBUG] TurnManager creation skipped (already created or no players).")
            return

        if self.route_finder is None:
            roads_dict = {road.id: road for road in self.roads}
            self.route_finder = RouteFinder(
                self.ev_manager,
                nodes=self.nodes,
                roads=roads_dict,
                routes=self.routes,
            )
            print(f"[DEBUG] RouteFinder initialized with {len(self.nodes)} nodes and {len(roads_dict)} roads.")

        first_player = min(self.players.values(), key=lambda item: item.turn_order)
        self.turn_manager = TurnManager(
            ev_manager=self.ev_manager,
            players=self.players,
            route_finder=self.route_finder,
            game_id=str(getattr(first_player, "game_id", "demo")),
            ui_manager=self.ui_manager,
            assets=self.assets,
            map_view=self.game_map,
        )

    def enter(self):
        print("\n" + "=" * 50)
        print("[DEBUG] GameScene enter() starting...")

        screen = pygame.display.get_surface()
        screen_width, screen_height = screen.get_size() if screen else (1200, 900)
        column_left = round(screen_width * 0.75)
        inventory_height = max(180, min(510, screen_height - 390))
        controls_y = 20 + inventory_height + 20

        if self.exit_button is None:
            self.exit_button = Button(
                pygame.Rect(10, 10, 100, 40),
                callback=lambda: self.ev_manager.post(
                    game_events.ChangeSceneEvent("menu")
                ),
                text="Exit",
                font=self.assets.font("default"),
                z_index=10,
            )
            self.elements.append(self.exit_button)

        if self.dice_button is None:
            self.dice_button = Button(
                pygame.Rect(column_left, controls_y + 70, 200, 60),
                callback=self.roll_dice,
                text="ROLL DICE",
                font=self.assets.font("default"),
                z_index=10,
                color=(0, 100, 200),
                hover_color=(0, 150, 255),
            )
            self.elements.append(self.dice_button)

        if self.dice_text is None:
            self.dice_text = Text(
                pygame.Rect(column_left, controls_y, 200, 50),
                fontsize=30,
                fontcolor=(255, 255, 255),
                text="0",
            )
            self.elements.append(self.dice_text)

        if self.map_controller is None:
            self.map_controller = MapController(self.ev_manager, self.ui_manager)
            print("[DEBUG] MapController initialized.")

        if self.map_surface is None:
            self.map_surface = pygame.Rect(50, 50, 800, 800)

        if self.map_container is None:
            self.map_container = pygame.Rect(50, 50, 800, 800)

        if self.map_projector is None:
            map_texture = self.assets.image("map")
            self.map_projector = MapProjector(
                map_bounds=(-28.6410763889, -35.5, 60.0, 62.3222216667),
                image_size=map_texture.get_size(),
            )
            print(
                f"[DEBUG] MapProjector initialized for texture {map_texture.get_size()} "
                "with bounds (min_lon, min_lat, max_lon, max_lat)="
                "(-28.6411, -35.5, 60.0, 62.3222)."
            )

        db_connected = self.db_connector is not None and self.db_connector.connection is not None
        print(f"[DEBUG] DB Connector status: {'CONNECTED' if db_connected else 'NOT CONNECTED / NONE'}")

        if db_connected:
            self._load_map_from_db(self.db_connector)
            game_id = self.db_connector.insert_game()
            print(f"[DEBUG] New Game created in database with Game ID: {game_id}")
            self._create_two_players(self.db_connector, game_id)

        if not self.nodes:
            print("[WARNING] No map nodes available from DB! Triggering fallback single-node setup...")
            fallback_node = Node(
                "1147",
                36.691002,
                3.215410,
                self.map_projector,
                is_waypoint=False,
                is_capital=False,
                radius=12,
                color=(255, 10, 10),
                font=self.assets.font("default"),
            )
            self.nodes = {"1147": fallback_node}
            self._create_demo_player()

        if self.game_map is None:
            self.game_map = Map(
                rect=self.map_surface,
                z_index=1,
                ev_manager=self.ev_manager,
                color=(20, 100, 0),
                container=self.map_container,
                texture=self.assets.image("map"),
                nodes=self.map_nodes or list(self.nodes.values()),
                roads=self.roads,
                players=list(self.players.values()),
                ui_manager=self.ui_manager,
            )
            self.elements.append(self.game_map)
            print(f"[DEBUG] Game Map element created with {len(self.nodes)} rendered nodes.")

        self._create_player_hud()
        self._create_turn_manager()

        print("[DEBUG] GameScene enter() initialization complete.")
        print("=" * 50 + "\n")

        super().enter()
