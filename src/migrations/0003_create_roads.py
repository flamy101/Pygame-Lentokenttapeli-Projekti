from yoyo import step


def apply_seed(conn):
    cursor = conn.cursor()

    # 1. Clean the slate (Execute statements ONE BY ONE to avoid syntax errors)
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE route_segments")
    cursor.execute("TRUNCATE TABLE routes")
    cursor.execute("TRUNCATE TABLE roads")
    cursor.execute("TRUNCATE TABLE road_types")
    cursor.execute("DELETE FROM nodes WHERE is_waypoint = 1")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    # 2. Base Road Types
    cursor.execute("""
                   INSERT INTO road_types (id, name, cost_per_step, speed) VALUES
                                                                               (1, 'land', 0, 1),
                                                                               (2, 'sea', 100, 1),
                                                                               (3, 'flight', 300, 1)
                   """)

    # 3. Python Helper to calculate GPS and insert nodes/routes
    def seed_route(start_id, end_id, road_type, num_waypoints):
        # Fetch coordinates for interpolation
        cursor.execute("SELECT lat, lon FROM nodes WHERE id = %s", (start_id,))
        start_row = cursor.fetchone()
        cursor.execute("SELECT lat, lon FROM nodes WHERE id = %s", (end_id,))
        end_row = cursor.fetchone()

        # Safely handle tuple vs dict cursor returns based on your driver
        start_lat = float(
            start_row["lat"] if isinstance(start_row, dict) else start_row[0]
        )
        start_lon = float(
            start_row["lon"] if isinstance(start_row, dict) else start_row[1]
        )
        end_lat = float(end_row["lat"] if isinstance(end_row, dict) else end_row[0])
        end_lon = float(end_row["lon"] if isinstance(end_row, dict) else end_row[1])

        # Insert Base Routes (Logical paths for the player)
        cursor.execute(
            "INSERT INTO routes (start_node_id, end_node_id, road_type_id) VALUES (%s, %s, %s)",
            (start_id, end_id, road_type),
        )
        route_fwd = cursor.lastrowid

        cursor.execute(
            "INSERT INTO routes (start_node_id, end_node_id, road_type_id) VALUES (%s, %s, %s)",
            (end_id, start_id, road_type),
        )
        route_bwd = cursor.lastrowid

        prev_node = start_id

        # Generate intermediate waypoints (The black dots you roll dice to land on)
        for i in range(1, num_waypoints + 1):
            fraction = i / (num_waypoints + 1)
            lat = start_lat + (end_lat - start_lat) * fraction
            lon = start_lon + (end_lon - start_lon) * fraction

            wp_name = f"WP-{start_id}-{end_id}#{i}"

            # Insert Map Node
            cursor.execute(
                "INSERT INTO nodes (name, lat, lon, is_capital, is_waypoint, region) VALUES (%s, %s, %s, 0, 1, 'Wilderness')",
                (wp_name, lat, lon),
            )
            curr_node = cursor.lastrowid

            # Insert Physical Edge (Road)
            cursor.execute(
                "INSERT INTO roads (node_a_id, node_b_id, road_type_id, cost) VALUES (%s, %s, %s, 0)",
                (prev_node, curr_node, road_type),
            )
            road_id = cursor.lastrowid

            # Bind Route Segments (So the route knows which roads to follow in order)
            cursor.execute(
                "INSERT INTO route_segments (route_id, road_id, seq) VALUES (%s, %s, %s)",
                (route_fwd, road_id, i),
            )
            cursor.execute(
                "INSERT INTO route_segments (route_id, road_id, seq) VALUES (%s, %s, %s)",
                (route_bwd, road_id, num_waypoints + 2 - i),
            )

            prev_node = curr_node

        # Final physical connection to the end city
        cursor.execute(
            "INSERT INTO roads (node_a_id, node_b_id, road_type_id, cost) VALUES (%s, %s, %s, 0)",
            (prev_node, end_id, road_type),
        )
        road_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO route_segments (route_id, road_id, seq) VALUES (%s, %s, %s)",
            (route_fwd, road_id, num_waypoints + 1),
        )
        cursor.execute(
            "INSERT INTO route_segments (route_id, road_id, seq) VALUES (%s, %s, %s)",
            (route_bwd, road_id, 1),
        )

    # 4. Execute the network build
    # --- SEA ROUTES (100 cost) ---
    seed_route(1192, 1193, 2, 3)
    seed_route(1193, 1190, 2, 2)
    seed_route(1190, 1191, 2, 1)
    seed_route(1191, 1185, 2, 4)
    seed_route(1185, 1180, 2, 3)
    seed_route(1180, 1181, 2, 2)
    seed_route(1181, 1184, 2, 3)
    seed_route(1184, 1198, 2, 2)
    seed_route(1198, 1195, 2, 3)
    seed_route(1195, 1196, 2, 4)
    seed_route(1196, 1199, 2, 3)
    seed_route(1199, 1178, 2, 2)
    seed_route(1178, 1192, 2, 2)

    # --- LAND ROUTES (0 cost) ---
    seed_route(1192, 1189, 1, 3)
    seed_route(1189, 1179, 1, 2)
    seed_route(1179, 1186, 1, 3)
    seed_route(1186, 1200, 1, 4)
    seed_route(1200, 1196, 1, 3)
    seed_route(1200, 1194, 1, 2)
    seed_route(1194, 1197, 1, 1)
    seed_route(1197, 1198, 1, 3)
    seed_route(1186, 1185, 1, 4)
    seed_route(1185, 1188, 1, 3)
    seed_route(1188, 1182, 1, 2)
    seed_route(1182, 1183, 1, 1)
    seed_route(1183, 1187, 1, 1)
    seed_route(1187, 1181, 1, 2)
    seed_route(1182, 1180, 1, 3)
    seed_route(1189, 1190, 1, 2)
    seed_route(1179, 1191, 1, 3)

    # --- FLIGHTS (300 cost, 0 waypoints = direct travel) ---
    seed_route(1178, 1179, 3, 0)
    seed_route(1196, 1200, 3, 0)
    seed_route(1199, 1186, 3, 0)
    seed_route(1194, 1184, 3, 0)
    seed_route(1185, 1183, 3, 0)
    seed_route(1180, 1188, 3, 0)
    seed_route(1192, 1189, 3, 0)
    seed_route(1198, 1181, 3, 0)


def rollback_seed(conn):
    """Allows 'yoyo rollback' to safely undo the seed."""
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE route_segments")
    cursor.execute("TRUNCATE TABLE routes")
    cursor.execute("TRUNCATE TABLE roads")
    cursor.execute("TRUNCATE TABLE road_types")
    cursor.execute("DELETE FROM nodes WHERE is_waypoint = 1")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")


# Yoyo requires the steps array to know what to run
steps = [step(apply_seed, rollback_seed)]
