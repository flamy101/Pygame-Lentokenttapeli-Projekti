def create_game(connection, name):
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO games ()
        VALUES ()
    """)

    game_id = cursor.lastrowid

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

    cursor.execute("""
        INSERT INTO players (
            game_id,
            name,
            color,
            money,
            current_node_id,
            turn_order,
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        game_id,
        name,
        "blue",
        0,
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
            latitude,
            longitude,
            airport_ident
        )
        VALUES (?, ?, ?, ?)
    """, (name, latitude, longitude, airport_ident))

    connection.commit()

    return cursor.lastrowid
