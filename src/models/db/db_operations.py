def create_game(
    connection,
    name: str = "Player 1",
    player_count: int = 2,
    start_node_id: int | None = None,
    starting_money: int = 300,
) -> int:
    """Create a new game record in MariaDB.

    :param connection: Active MariaDB database connection.
    :param name: Initial player name.
    :param player_count: Total player count for the match.
    :param start_node_id: Explicit starting node ID override.
    :param starting_money: Initial money for the new player.
    :return: Generated game ID.
    """
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO games (current_turn, is_finished)
        VALUES (0, 0)
    """)

    game_id = cursor.lastrowid

    if start_node_id is None:
        cursor.execute("""
            SELECT id
            FROM nodes
            ORDER BY id
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("No nodes exist in the database")
        current_node_id = row[0]
    else:
        current_node_id = start_node_id

    cursor.execute("""
        INSERT INTO players (
            game_id,
            name,
            color,
            money,
            current_node_id,
            turn_order
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        game_id,
        name,
        "blue",
        starting_money,
        current_node_id,
        1
    ))

    connection.commit()
    return game_id


def create_node(connection, name, latitude, longitude, airport_ident):
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO nodes (
            name,
            lat,
            lon,
            airport_ident
        )
        VALUES (%s, %s, %s, %s)
    """, (name, latitude, longitude, airport_ident))

    connection.commit()
    return cursor.lastrowid


def get_all_token_types(connection) -> list[dict]:
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, name, category, money_delta, weight, texture_key FROM token_types")
    return cursor.fetchall() or []


def clear_node_tokens(connection):
    cursor = connection.cursor()
    cursor.execute("DELETE FROM node_tokens")
    connection.commit()


def insert_node_tokens(connection, assignments: list[tuple[int, int]]):
    cursor = connection.cursor()
    query = "INSERT INTO node_tokens (node_id, token_type_id, is_claimed) VALUES (%s, %s, 0)"
    cursor.executemany(query, assignments)
    connection.commit()