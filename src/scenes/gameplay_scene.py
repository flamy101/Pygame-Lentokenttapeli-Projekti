import random
from collections import defaultdict
import pygame
import events as base_events

from controllers.dice_roller import DiceRoller
from controllers.map_controller import MapController
from controllers.map_projector import MapProjector
from controllers.route_finder import RouteFinder
from controllers.turn_manager import TurnManager
from entities.map_node import Node
from entities.player import Player
from entities.road import Road
from entities.route import Route
from entities.token import Token
import game_events
from scenes import Scene
from ui.elements import Button, CurrentPlayerBadge, DiceDisplay
from ui.map import Map
from ui.player_hud import PlayerHUD
from ui.popup import UIPopup


class GameScene(Scene):
    SIDEBAR_COLOR = (66, 57, 52)

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
        self.game_id = None
        self.notification_text = ""
        self.notification_seconds = 0.0
        self.winner_id = None

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

        if player.pending_token is not None and self.route_finder is not None:
            self.route_finder.suppress_next_roll(player.id)

        print(f"[DEBUG] Rolling dice for Player {player.id} (at node {player.current_node.id})...")
        self.ev_manager.post(
            game_events.RollRequestedEvent(
                player.id,
                current_node_id=player.current_node.id,
            )
        )

    def notify(self, event):
        if isinstance(event, base_events.TickEvent):
            self.notification_seconds = max(0.0, self.notification_seconds - event.dt)
            if self.dice_text is not None:
                self.dice_text.update(event.dt)
            return

        if isinstance(event, game_events.CurrentPlayerChangedEvent):
            player = self._lookup_player(event.player_id)
            self._show_notification(f"{player.name}'s turn")
            return

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
            if current_player.pending_token is not None:
                token = current_player.pending_token
                node = self.nodes.get(str(current_player.pending_token_node_id))
                if event.value >= 4 and node is not None:
                    self._show_notification(
                        f"{current_player.name} rolled {event.value}: token opened (4–6)"
                    )
                    current_player.pending_token = None
                    current_player.pending_token_node_id = None
                    self._reveal_token(current_player, node, token)
                else:
                    self._show_notification(
                        f"{current_player.name} rolled {event.value}: no 4–6; turn passes"
                    )
                    # The token remains unclaimed on the airport, but this
                    # player's roll attempt is complete; do not carry it into
                    # their next turn as a stale pending roll.
                    current_player.pending_token = None
                    current_player.pending_token_node_id = None
                    self._show_token_result(
                        current_player, node, token,
                        "You need a 4, 5, or 6 to open this token. The token stays here.",
                        resolve=True,
                        image=self.assets.image("token-backside"),
                    )
                return
        elif isinstance(event, game_events.PlayerArrivedEvent):
            if self.winner_id is not None:
                return
            player = self._lookup_player(event.player_id)
            node = self.nodes.get(str(event.city_node_id))
            if node is not None:
                has_star = player.has_star or any(
                    "star of africa" in item_name.lower()
                    for item_name in player.items
                )
                if has_star and self._is_victory_node(node):
                    player.has_won = True
                    self.winner_id = player.id
                    if self.db_connector is not None:
                        try:
                            self.db_connector.set_player_won(player.id)
                            self.db_connector.set_game_finished(int(player.game_id))
                        except Exception as error:
                            print(f"[WARNING] Could not persist the win to the database: {error}")
                    self._show_win_modal(player, node)
                    return
                self._offer_airport_token(player, node)
        elif isinstance(event, game_events.TokenResolvedEvent):
            return

    def _show_notification(self, message: str, duration: float = 3.0):
        self.notification_text = message
        self.notification_seconds = duration
        print(f"[NOTICE] {message}")

    def draw(self, screen: pygame.Surface):
        super().draw(screen)
        if self.notification_seconds <= 0 or not self.notification_text:
            return
        font = self.assets.font("default")
        text = font.render(self.notification_text, True, (255, 248, 225))
        panel = pygame.Rect(0, 0, min(screen.get_width() - 32, text.get_width() + 36), text.get_height() + 22)
        panel.midtop = (screen.get_width() // 2, 18)
        background = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(background, (35, 27, 25, 225), background.get_rect(), border_radius=8)
        pygame.draw.rect(background, (222, 169, 87, 255), background.get_rect(), 2, border_radius=8)
        screen.blit(background, panel.topleft)
        screen.blit(text, text.get_rect(center=panel.center))

    def _popup_rect(self):
        screen = pygame.display.get_surface()
        width, height = screen.get_size() if screen else (1200, 900)
        return pygame.Rect(width // 2 - 230, height // 2 - 130, 460, 260)

    @staticmethod
    def _is_victory_node(node):
        """Recognize Cairo and Tangier whether the map uses city or airport names."""
        normalize = lambda value: "".join(
            character for character in str(value or "").lower()
            if character.isalnum()
        )
        name = normalize(node.name)
        region = normalize(getattr(node, "region", ""))
        airport_ident = normalize(getattr(node, "airport_ident", ""))
        return (
            name.startswith(("cairo", "tangier"))
            or region in {"cairo", "tangier"}
            or airport_ident in {"cai", "heca", "tng", "gmtt"}
        )

    def _show_win_modal(self, player, node):
        print(f"[NOTICE] {player.name} wins by bringing the Star of Africa to {node.name}.")
        if self.ui_manager is None:
            return

        def exit_to_menu():
            self.ui_manager.close_modal()
            self.ev_manager.post(game_events.ChangeSceneEvent("menu"))

        self.ui_manager.open_modal(
            UIPopup(
                self.ev_manager,
                self._popup_rect(),
                self.assets,
                f"{player.name} wins! The Star of Africa has reached {node.name}.",
                [("Exit to Menu", exit_to_menu)],
                image=self.assets.image("token-empty"),
            )
        )
        if self.turn_manager is not None:
            self.turn_manager.awaiting_token_resolution = True

    def _offer_airport_token(self, player, node):
        token = next((item for item in node.tokens if not item.is_claimed), None)
        if token is None or self.ui_manager is None or self.ui_manager.modal is not None:
            return

        def wait_for_roll():
            self.ui_manager.close_modal()
            player.pending_token = token
            player.pending_token_node_id = node.id
            if self.turn_manager is not None:
                self.turn_manager.awaiting_token_resolution = False
            self._show_notification(
                f"{player.name} is rolling to open the token. A 4–6 succeeds.",
                duration=4.0,
            )
            self.roll_dice()

        def skip():
            self.ui_manager.close_modal()
            self.ev_manager.post(game_events.TokenResolvedEvent(player.id, node.id))

        buttons = [("Roll 4–6", wait_for_roll), ("Leave token", skip)]
        if player.money >= 100:
            def pay_and_open():
                self.ui_manager.close_modal()
                player.money -= 100
                if self.db_connector is not None:
                    self.db_connector.update_player_money(player.id, -100)
                self._reveal_token(player, node, token)
            buttons.insert(0, ("Open for £100", pay_and_open))
        self.ui_manager.open_modal(UIPopup(
            self.ev_manager, self._popup_rect(), self.assets,
            f"{player.name} reached {node.name or 'an airport'}. Open the hidden token?",
            buttons,
        ))
        if self.turn_manager is not None:
            self.turn_manager.awaiting_token_resolution = True

    def _show_token_result(self, player, node, token, message, resolve=False, image=None):
        if self.ui_manager is None:
            if resolve:
                self.ev_manager.post(game_events.TokenResolvedEvent(player.id, node.id))
            return
        def finish():
            self.ui_manager.close_modal()
            if resolve:
                self.ev_manager.post(game_events.TokenResolvedEvent(player.id, node.id))
        self.ui_manager.open_modal(UIPopup(
            self.ev_manager, self._popup_rect(), self.assets, message,
            [("Continue", finish)], image=token.texture if image is None else image,
        ))
        if self.turn_manager is not None:
            self.turn_manager.awaiting_token_resolution = True

    def _reveal_token(self, player, node, token):
        if token.is_claimed:
            return
        token.is_claimed = True
        if self.db_connector is not None:
            self.db_connector.claim_node_token(token.id)
        category = token.category.lower()
        message = f"{player.name} found {token.token_type}."
        if "star" in token.token_type.lower():
            player.has_star = True
            player.add_item(token.token_type, token.texture_key)
            message += " You found the Star of Africa! Bring it to Cairo or Tangier to win."
        elif "horseshoe" in token.token_type.lower():
            if any(other.has_star for other in self.players.values()):
                player.has_horseshoe = True
                player.add_item(token.token_type, token.texture_key)
                message += " The horseshoe can protect the Star of Africa from a robber."
            else:
                message += " The horseshoe is discarded because the Star has not been found."
        elif category in {"gem", "treasure", "money", "reward"}:
            player.money += token.money_delta
            message += f" You receive £{token.money_delta}."
            player.add_item(token.token_type, token.texture_key)
            if self.db_connector is not None:
                self.db_connector.update_player_money(player.id, token.money_delta)
        elif category in {"robber", "bandit", "hazard"}:
            if player.has_star and player.has_horseshoe:
                player.has_horseshoe = False
                if player.items.get("Horseshoe", {}).get("quantity", 0):
                    player.items["Horseshoe"]["quantity"] -= 1
                    if self.db_connector is not None:
                        self.db_connector.remove_player_item(player.id, "Horseshoe")
                message += " Your horseshoe protects the Star from the robber."
            else:
                lost = player.money
                player.money = 0
                message += f" The robber takes £{lost}."
                if self.db_connector is not None and lost:
                    self.db_connector.update_player_money(player.id, -lost)
            player.add_item(token.token_type, token.texture_key)
        elif category == "empty" or token.token_type.lower() == "empty":
            player.add_item(token.token_type, token.texture_key)
            message += " The token is empty."
        self._show_token_result(player, node, token, message, resolve=True)

    def _lookup_player(self, player_id):
        if player_id in self.players:
            return self.players[player_id]
        for player in self.players.values():
            if player.id == player_id:
                return player
        raise KeyError(f"No player found for turn id {player_id!r}")

    def _sidebar_column_left(self, screen_width):
        margin = 20
        map_right = self.map_container.right if self.map_container else 850
        return max(round(screen_width * 0.75), map_right + margin)

    def draw(self, screen):
        column_left = self._sidebar_column_left(screen.get_width())
        sidebar_left = max(0, column_left - 20)
        pygame.draw.rect(
            screen,
            self.SIDEBAR_COLOR,
            pygame.Rect(sidebar_left, 0, screen.get_width() - sidebar_left, screen.get_height()),
        )
        super().draw(screen)

    def _load_map_from_db(self, db):
        """Fetch nodes and roads from MariaDB and map them to Node objects."""
        print("[DEBUG] DB Map Loading: Fetching nodes and roads from database...")
        raw_nodes = db.get_all_nodes()
        raw_roads = db.get_all_roads()
        raw_road_types = (
            db.get_all_road_types() if hasattr(db, "get_all_road_types") else []
        )
        raw_routes = db.get_all_routes() if hasattr(db, "get_all_routes") else []
        cost_by_road_type = {1: 0.0, 2: 100.0, 3: 300.0}
        cost_by_road_type.update(
            {
                int(row["id"]): float(row["cost_per_step"])
                for row in raw_road_types
            }
        )

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
                airport_ident=data.get("airport_ident"),
                radius=38 if not data.get("is_waypoint") else 26,
                color=(255, 200, 0) if data.get("is_capital") else (235, 235, 220),
                font=self.assets.font(
                    "small" if data.get("is_waypoint") else "airport"
                ),
            )

        for n_id, node in list(self.nodes.items())[:5]:
            px, py = self.map_projector(node.lat, node.lon)
            print(
                f"[DEBUG] Node {n_id} ({node.lat}, {node.lon}) -> projected px: ({px}, {py})"
            )

        self.roads = []
        roads_by_id = {}
        for r in raw_roads:
            node_a = self.nodes.get(str(r["node_a_id"]))
            node_b = self.nodes.get(str(r["node_b_id"]))
            if node_a and node_b:
                road_type_id = int(r.get("road_type_id", 1))
                road_type = {1: "land", 2: "sea", 3: "flight"}.get(
                    road_type_id, "land"
                )
                road = Road(
                    road_id=str(r["id"]),
                    node_a=node_a,
                    node_b=node_b,
                    road_type=road_type,
                    cost=float(r.get("cost") or cost_by_road_type.get(road_type_id, 0)),
                )
                self.roads.append(road)
                roads_by_id[road.id] = road


        self.map_nodes = [
            node for node_id, node in self.nodes.items() if node_id in road_node_ids
        ]

        self.routes = {}
        for row in raw_routes:
            start_node = self.nodes.get(str(row["start_node_id"]))
            end_node = self.nodes.get(str(row["end_node_id"]))
            if start_node is None or end_node is None:
                continue

            route_id = str(row["id"])
            segment_rows = db.get_route_segments(row["id"])
            segments = [
                roads_by_id[str(segment["road_id"])]
                for segment in segment_rows
                if str(segment["road_id"]) in roads_by_id
            ]
            road_type_id = int(row.get("road_type_id", 1))
            route = Route(
                route_id=route_id,
                start_node=start_node,
                end_node=end_node,
                road_type={1: "land", 2: "sea", 3: "flight"}.get(
                    road_type_id, "land"
                ),
                segments=segments,
            )
            self.routes[route_id] = route

        self._separate_parallel_corridors()

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
            f"{len(self.map_nodes)} board nodes, {len(self.roads)} drawable roads, "
            f"{len(self.routes)} routes."
        )

    def _separate_parallel_corridors(self):
        """Give alternate transport types between the same cities distinct lanes.

        Waypoints on multi-hop routes are shifted as a connected corridor. Direct
        routes get a quadratic curve, keeping their endpoints fixed.
        """
        corridors = defaultdict(lambda: defaultdict(list))
        for route in self.routes.values():
            city_ids = tuple(sorted((str(route.start_node.id), str(route.end_node.id))))
            corridors[city_ids][route.road_type].append(route)

        moved_waypoints = set()
        parallel_count = 0
        for city_ids, by_type in corridors.items():
            road_types = sorted(by_type)
            if len(road_types) < 2:
                continue
            parallel_count += 1
            low_node = self.nodes[city_ids[0]]
            high_node = self.nodes[city_ids[1]]
            dx = high_node.pos_x - low_node.pos_x
            dy = high_node.pos_y - low_node.pos_y
            length = (dx * dx + dy * dy) ** 0.5
            if length == 0:
                print(f"[WARNING] Parallel corridor {city_ids} has coincident city coordinates.")
                continue
            normal_x, normal_y = -dy / length, dx / length
            lane_offsets = {
                road_type: (index - (len(road_types) - 1) / 2) * 80.0
                for index, road_type in enumerate(road_types)
            }

            for road_type, routes in by_type.items():
                lane_offset = lane_offsets[road_type]
                seen_roads = set()
                for route in routes:
                    current = route.start_node
                    path_nodes = [current]
                    for road in route.segments:
                        try:
                            current = road.get_other_node(current)
                        except ValueError:
                            print(
                                f"[WARNING] Route {route.id} is disconnected at road {road.id}; "
                                "lane offset skipped for its remaining path."
                            )
                            break
                        path_nodes.append(current)
                        if road.id not in seen_roads:
                            seen_roads.add(road.id)
                            if len(path_nodes) == 2 and len(route.segments) == 1:
                                orientation = 1 if str(road.node_a.id) == city_ids[0] else -1
                                road.set_curve(orientation * lane_offset * 2)

                    for node in path_nodes[1:-1]:
                        if node.is_waypoint and node.id not in moved_waypoints:
                            node.pos_x = round(node.pos_x + normal_x * lane_offset)
                            node.pos_y = round(node.pos_y + normal_y * lane_offset)
                            moved_waypoints.add(node.id)

                print(
                    f"[DEBUG] Road lane {low_node.name or city_ids[0]} "
                    f"({city_ids[0]}) -> {high_node.name or city_ids[1]} "
                    f"({city_ids[1]}) "
                    f"({road_type}): offset {lane_offset:+.0f}px, "
                    f"{len(seen_roads)} physical segment(s)."
                )

        # Rebuild all roads after waypoint positions have settled. A direct,
        # curved road can also be shared by a multi-hop route, so rebuilding
        # only the multi-hop roads leaves stale endpoints in that case.
        direct_road_ids = {
            segment.id
            for by_type in corridors.values()
            for routes in by_type.values()
            for route in routes
            if len(route.segments) == 1
            for segment in route.segments
        }
        for road in self.roads:
            if road.id in direct_road_ids:
                # Preserve the lane curve while baking against the final node
                # coordinates (one of its endpoints may have moved).
                road.set_curve(road.curve)
            else:
                road.set_curve(0.0)

        # Route preview lines cache their polyline and distances from the road
        # geometry, so refresh them after all roads have been rebuilt.
        for route in self.routes.values():
            route._bake_route_geometry()

        misaligned_roads = [
            road.id
            for road in self.roads
            if not road.points
            or road.points[0] != (road.node_a.pos_x, road.node_a.pos_y)
            or road.points[-1] != (road.node_b.pos_x, road.node_b.pos_y)
        ]
        if misaligned_roads:
            print(
                f"[WARNING] {len(misaligned_roads)} road geometries have endpoints "
                f"misaligned with their waypoints: {misaligned_roads}"
            )
        else:
            print(
                f"[DEBUG] Road geometry endpoint alignment OK "
                f"({len(self.roads)} roads checked)."
            )

        print(
            f"[DEBUG] Parallel road diagnostics: {parallel_count} city corridors "
            f"with alternate transport types; {len(moved_waypoints)} waypoints adjusted."
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
            db_connector=db,
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
            db_connector=db,
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
        column_left = self._sidebar_column_left(screen_width)
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
        column_left = self._sidebar_column_left(screen_width)
        inventory_height = max(180, min(510, screen_height - 390))
        controls_y = 20 + inventory_height + 20
        dice_width = min(240, max(160, screen_width - column_left - 30))
        dice_x = column_left + max(0, (screen_width - column_left - dice_width) // 2)

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
                pygame.Rect(dice_x - 10, controls_y + 92, dice_width + 20, 68),
                callback=self.roll_dice,
                text="ROLL DICE",
                font=self.assets.font("default"),
                z_index=10,
                color=(145, 74, 47),
                hover_color=(180, 98, 58),
                text_color=(255, 244, 213),
                border_color=(224, 180, 104),
                border_width=3,
                border_radius=10,
            )
            self.elements.append(self.dice_button)

        if self.dice_text is None:
            self.dice_text = DiceDisplay(
                pygame.Rect(dice_x, controls_y, dice_width, 78),
                font=self.assets.font("dice"),
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
            map_control_points = {
                "nw": (32.0919611667, -28.6471293333),
                "ne": (31.2895921667, 61.8606971667),
                "se": (-32.8112481667, 62.4811053333),
                "sw": (-26.1668358333, -25.1878980000),
                "center": (1.7008826667, 16.9950613333),
            }
            self.map_projector = MapProjector.from_control_points(
                map_texture.get_size(), map_control_points, scale_y=0.79, scale_x=1.1
            )
            print(
                f"[DEBUG] Georeferenced MapProjector initialized for texture "
                f"{map_texture.get_size()} from 5 control points "
                f"(horizontal scale {self.map_projector.scale_x:.2f}, "
                f"vertical scale {self.map_projector.scale_y:.2f})."
            )

        db_connected = self.db_connector is not None and self.db_connector.connection is not None
        print(f"[DEBUG] DB Connector status: {'CONNECTED' if db_connected else 'NOT CONNECTED / NONE'}")

        if db_connected:
            self._load_map_from_db(self.db_connector)
            game_id = self.db_connector.insert_game()
            self.game_id = game_id
            print(f"[DEBUG] New Game created in database with Game ID: {game_id}")
            self._create_two_players(self.db_connector, game_id)
            self._seed_game_tokens(self.db_connector, game_id)

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

    def _seed_game_tokens(self, db, game_id):
        city_nodes = [node for node in self.map_nodes if not node.is_waypoint]
        city_ids = [int(node.id) for node in city_nodes if str(node.id).isdigit()]
        if not city_ids:
            return
        count = db.seed_game_tokens(game_id, city_ids)
        for row in db.get_game_node_tokens(game_id):
            node = self.nodes.get(str(row["node_id"]))
            if node is None:
                continue
            key = row.get("texture_key") or "token-empty"
            images = getattr(self.assets, "images", {})
            token = Token(
                id=row["node_token_id"],
                token_type=(
                    "Star of Africa"
                    if key == "merkki-bitcoin-lvl3"
                    else row["name"]
                ),
                category=row["category"],
                money_delta=int(row.get("money_delta") or 0),
                texture=images.get(key) or images.get("token-empty"),
                texture_key=key,
                back_texture=images.get("token-backside"),
                is_claimed=bool(row.get("is_claimed")),
            )
            node.tokens.append(token)
        print(f"[DEBUG] Seeded and rendered {count} hidden tokens for game {game_id}.")
