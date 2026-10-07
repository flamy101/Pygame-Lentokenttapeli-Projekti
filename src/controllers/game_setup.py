import game_events
from controllers.turn_manager import TurnManager


class GameSetup:
    """
    Controller responsible for initializing a new game session.
    Creates DB records for the game and players, loads static board topology,
    and initializes the TurnManager.
    """

    def __init__(self, ev_manager, db_connector):
        self.ev_manager = ev_manager
        self.db = db_connector

        self.nodes = {}
        self.road_types = {}
        self.roads = {}
        self.routes = {}

        self.turn_manager = None

    def setup_new_game(
        self,
        player_count: int,
        players_info: list[tuple[str, str]],
        start_node_id: int,
        starting_money: int,
    ):
        """
        Creates a new game, persists it to the database, caches board data,
        and posts GameStartedEvent.

        :param players_info: A list of (name, color) tuples.
        """
        if len(players_info) != player_count:
            raise ValueError(
                f"Expected {player_count} players, but received {len(players_info)} configurations."
            )

        try:
            game_id = self.db.insert_game()

            for turn_order, (name, color) in enumerate(players_info):
                self.db.insert_player(
                    game_id=game_id,
                    name=name,
                    color=color,
                    money=starting_money,
                    current_node_id=start_node_id,
                    turn_order=turn_order,
                )

            players_data = self.db.get_players_by_game(game_id)

            self._load_static_board_data()
            self.turn_manager = TurnManager(self.ev_manager, players_data)
            self.ev_manager.post(game_events.GameStartedEvent(game_id=game_id))

        except Exception as e:
            raise RuntimeError(f"Failed to setup game session: {e}") from e

    def _load_static_board_data(self):
        """Fetches nodes, road_types, roads, and routes from DB using DBConnector methods."""

        self.nodes = {row["id"]: row for row in self.db.get_all_nodes()}
        self.road_types = {row["id"]: row for row in self.db.get_all_road_types()}
        self.roads = {row["id"]: row for row in self.db.get_all_roads()}
        self.routes = {row["id"]: row for row in self.db.get_all_routes()}

        for route_id, route in self.routes.items():
            route["segments"] = self.db.get_route_segments(route_id)

    def get_node(self, node_id: int) -> dict:
        return self.nodes.get(node_id)

    def get_route(self, route_id: int) -> dict:
        return self.routes.get(route_id)
