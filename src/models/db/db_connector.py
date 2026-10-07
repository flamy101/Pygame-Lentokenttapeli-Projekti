import mariadb
from dotenv import load_dotenv
from os import getenv

import events

from models.db import db_operations

load_dotenv()

class DBConnector:
    def __init__(self, ev_manager):
        self.ev_manager = ev_manager
        self.ev_manager.register_listener(self)
        self.connection : mariadb.Connection = None  # ty: ignore[invalid-assignment]


    def notify(self, event):
        match event:
            case events.PygameReadyEvent():
                print("Checking for connection...")
                self.is_connected()




    def is_connected(self):
        if getenv("DEBUG") == "TRUE":
            return

        try:
            self.connection: mariadb.Connection = mariadb.connect(
                host = getenv("DB_HOST"),
                port = int(getenv("DB_PORT")),  # ty: ignore[invalid-argument-type]
                user = getenv("DB_USER"),
                password = getenv("DB_PASSWORD"),
                database = getenv("DB_NAME"),
            )

            event = events.DBConnect(True)

        except mariadb.Error as error:

            print(f"MariaDB error: {error}")
            event = events.DBConnect(False)
            event = events.DatabaseConnectionFailed(True)

        self.ev_manager.post(event)



    def create_new_game(self):
        game_id = db_operations.create_game(self.connection, "masha")
        return game_id


    # HELPERS
    def _fetch_all(self, query: str, params: tuple = ()) -> list[dict]:
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchall() or []
        finally:
            cursor.close()

    def _fetch_one(self, query: str, params: tuple = ()) -> dict:
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        finally:
            cursor.close()

    def _execute(self, query: str, params: tuple = ()) -> int:
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.lastrowid
        finally:
            cursor.close()


    # NODES
    def get_all_nodes(self) -> list[dict]:
        return self._fetch_all("SELECT * FROM nodes")

    def get_node(self, node_id: int) -> dict:
        return self._fetch_one("SELECT * FROM nodes WHERE id = %s", (node_id,))

    def get_nodes_by_region(self, region: str) -> list[dict]:
        return self._fetch_all("SELECT * FROM nodes WHERE region = %s", (region,))


    # ROAD TYPES
    def get_all_road_types(self) -> list[dict]:
        return self._fetch_all("SELECT * FROM road_types")

    def get_road_type(self, road_type_id: int) -> dict:
        return self._fetch_one(
            "SELECT * FROM road_types WHERE id = %s", (road_type_id,)
        )


    # ROADS
    def get_all_roads(self) -> list[dict]:
        return self._fetch_all("SELECT * FROM roads")

    def get_roads_from(self, node_id: int) -> list[dict]:
        return self._fetch_all(
            "SELECT * FROM roads WHERE node_a_id = %s OR node_b_id = %s",
            (node_id, node_id),
        )

    def get_road(self, road_id: int) -> dict:
        return self._fetch_one("SELECT * FROM roads WHERE id = %s", (road_id,))


    # ROUTES
    def get_all_routes(self) -> list[dict]:
        return self._fetch_all("SELECT * FROM routes")

    def get_route(self, route_id: int) -> dict:
        return self._fetch_one("SELECT * FROM routes WHERE id = %s", (route_id,))

    def get_route_segments(self, route_id: int) -> list[dict]:
        query = """
                SELECT
                    rs.id, rs.route_id, rs.road_id, rs.seq,
                    r.node_a_id, r.node_b_id, r.road_type_id, r.cost
                FROM route_segments rs
                         JOIN roads r ON rs.road_id = r.id
                WHERE rs.route_id = %s
                ORDER BY rs.seq ASC \
                """
        return self._fetch_all(query, (route_id,))

    def get_routes_from(self, node_id: int) -> list[dict]:
        return self._fetch_all(
            "SELECT * FROM routes WHERE start_node_id = %s", (node_id,)
        )


    # TOKEN TYPES / NODE TOKENS
    def get_all_token_types(self) -> list[dict]:
        return self._fetch_all("SELECT * FROM token_types")

    def get_token_type(self, token_type_id: int) -> dict:
        return self._fetch_one(
            "SELECT * FROM token_types WHERE id = %s", (token_type_id,)
        )

    def get_node_tokens(self, node_id: int) -> list[dict]:
        return self._fetch_all(
            "SELECT * FROM node_tokens WHERE node_id = %s AND is_claimed = 0",
            (node_id,),
        )

    def claim_node_token(self, node_token_id: int) -> None:
        self._execute(
            "UPDATE node_tokens SET is_claimed = 1 WHERE id = %s", (node_token_id,)
        )


    # GAMES
    def insert_game(self) -> int:
        return self._execute(
            "INSERT INTO games (current_turn, is_finished) VALUES (0, 0)"
        )

    def get_game(self, game_id: int) -> dict:
        return self._fetch_one("SELECT * FROM games WHERE id = %s", (game_id,))

    def update_game_turn(self, game_id: int, current_turn: int) -> None:
        self._execute(
            "UPDATE games SET current_turn = %s WHERE id = %s", (current_turn, game_id)
        )

    def set_game_finished(self, game_id: int) -> None:
        self._execute("UPDATE games SET is_finished = 1 WHERE id = %s", (game_id,))


    # PLAYERS
    def insert_player(
        self,
        game_id: int,
        name: str,
        color: str,
        money: int,
        current_node_id: int,
        turn_order: int,
    ) -> int:
        query = """
                INSERT INTO players (game_id, name, color, money, current_node_id, turn_order)
                VALUES (%s, %s, %s, %s, %s, %s) \
                """
        return self._execute(
            query, (game_id, name, color, money, current_node_id, turn_order)
        )

    def get_player(self, player_id: int) -> dict:
        return self._fetch_one("SELECT * FROM players WHERE id = %s", (player_id,))

    def get_players_by_game(self, game_id: int) -> list[dict]:
        return self._fetch_all(
            "SELECT * FROM players WHERE game_id = %s ORDER BY turn_order ASC",
            (game_id,),
        )

    def update_player_position(self, player_id: int, node_id: int) -> None:
        self._execute(
            "UPDATE players SET current_node_id = %s WHERE id = %s",
            (node_id, player_id),
        )

    def update_player_money(self, player_id: int, delta: int) -> None:
        self._execute(
            "UPDATE players SET money = money + %s WHERE id = %s", (delta, player_id)
        )

    def update_player_route(
        self, player_id: int, route_id: int | None, progress: int
    ) -> None:
        self._execute(
            "UPDATE players SET current_route_id = %s, route_progress = %s WHERE id = %s",
            (route_id, progress, player_id),
        )

    def set_player_eliminated(self, player_id: int) -> None:
        self._execute(
            "UPDATE players SET is_eliminated = 1 WHERE id = %s", (player_id,)
        )

    def set_player_won(self, player_id: int) -> None:
        self._execute("UPDATE players SET has_won = 1 WHERE id = %s", (player_id,))


    # PLAYER ITEMS
    def get_player_items(self, player_id: int) -> list[dict]:
        return self._fetch_all(
            "SELECT * FROM player_items WHERE player_id = %s", (player_id,)
        )

    def add_player_item(
        self, player_id: int, item_name: str, quantity: int = 1
    ) -> None:
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "UPDATE player_items SET quantity = quantity + %s WHERE player_id = %s AND item_name = %s",
                (quantity, player_id, item_name),
            )
            if cursor.rowcount == 0:
                cursor.execute(
                    "INSERT INTO player_items (player_id, item_name, quantity) VALUES (%s, %s, %s)",
                    (player_id, item_name, quantity),
                )
            self.connection.commit()
        finally:
            cursor.close()

    def remove_player_item(
        self, player_id: int, item_name: str, quantity: int = 1
    ) -> None:
        self._execute(
            "UPDATE player_items SET quantity = GREATEST(0, quantity - %s) WHERE player_id = %s AND item_name = %s",
            (quantity, player_id, item_name),
        )
