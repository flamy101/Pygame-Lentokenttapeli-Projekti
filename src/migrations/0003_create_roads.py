"""Import the user-authored Afrikan Tähti network without inventing nodes."""

import json
from pathlib import Path

from yoyo import step


__depends__ = {"0002_insert_nodes"}
# MariaDB DDL and TRUNCATE implicitly commit, so this migration must not run
# inside Yoyo's savepoint transaction wrapper.
__transactional__ = False

NETWORK_FILE = Path(__file__).with_name("boardgame_network_project_2026-10-07.json")
MAX_ROUTE_HOPS = 6


def _load_network():
    with NETWORK_FILE.open(encoding="utf-8") as source:
        data = json.load(source)
    return data


def _node_chains(data):
    """Trace the supplied road segments into airport-to-airport corridors."""
    nodes = {int(node["id"]): node for node in data["nodes"]}
    adjacency = {node_id: [] for node_id in nodes}
    road_by_id = {}
    for road in data["roads"]:
        road_id = int(road["id"])
        node_a = int(road["node_a_id"])
        node_b = int(road["node_b_id"])
        road_type = int(road["road_type_id"])
        if node_a not in nodes or node_b not in nodes:
            raise ValueError(f"Road {road_id} references a node absent from the JSON.")
        if road_type not in {int(item["id"]) for item in data["roadTypes"]}:
            raise ValueError(f"Road {road_id} references an unknown JSON road type.")
        road_by_id[road_id] = road
        adjacency[node_a].append((node_b, road_type, road_id))
        adjacency[node_b].append((node_a, road_type, road_id))

    airport_ids = {
        node_id
        for node_id, node in nodes.items()
        if not node["is_waypoint"] and node.get("airport_ident")
    }
    waypoints = {
        node_id for node_id, node in nodes.items() if node["is_waypoint"]
    }
    visited_roads = set()
    chains = []

    for start_id in sorted(airport_ids):
        for first_node, route_type, first_road in adjacency[start_id]:
            if first_road in visited_roads:
                continue

            chain_nodes = [start_id, first_node]
            chain_roads = [first_road]
            previous_node = start_id
            current_node = first_node

            while current_node not in airport_ids:
                if current_node not in waypoints:
                    raise ValueError(
                        f"Road chain from JSON node {start_id} reaches non-airport "
                        f"node {current_node}."
                    )
                exits = [
                    edge for edge in adjacency[current_node]
                    if edge[0] != previous_node
                ]
                if len(adjacency[current_node]) != 2 or len(exits) != 1:
                    raise ValueError(
                        f"JSON waypoint {current_node} must have exactly two road links."
                    )

                next_node, next_type, next_road = exits[0]
                if next_type != route_type:
                    raise ValueError(
                        f"Road type changes inside the authored path at waypoint {current_node}."
                    )
                if next_road in visited_roads or next_node == start_id:
                    raise ValueError("The supplied road network contains a waypoint-only loop.")

                chain_nodes.append(next_node)
                chain_roads.append(next_road)
                previous_node, current_node = current_node, next_node

            if current_node == start_id:
                raise ValueError("The supplied road network contains a self-loop.")
            visited_roads.update(chain_roads)
            chains.append((chain_nodes, chain_roads, route_type))

    if visited_roads != set(road_by_id):
        missing = sorted(set(road_by_id) - visited_roads)
        raise ValueError(f"Some supplied roads are not between airports: {missing}")

    return nodes, road_by_id, chains


def _airport_database_ids(cursor, source_nodes):
    id_map = {}
    for source_id, node in source_nodes.items():
        if node["is_waypoint"]:
            continue
        ident = node.get("airport_ident")
        if not ident:
            raise ValueError(f"Source airport node {source_id} has no airport_ident.")
        cursor.execute(
            "SELECT id FROM nodes WHERE airport_ident = %s AND is_waypoint = 0",
            (ident,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(
                f"Airport {ident} from the supplied network is not present in nodes."
            )
        id_map[source_id] = int(row["id"] if isinstance(row, dict) else row[0])
    return id_map


def _delete_imported_waypoints(cursor):
    # This network migration owns waypoint rows. Removing them before reimport
    # makes a retry safe after a non-transactional DDL/insert failure.
    cursor.execute("DELETE FROM nodes WHERE is_waypoint = 1")


def _seed_network(connection, data):
    source_nodes, source_roads, chains = _node_chains(data)
    cursor = connection.cursor()
    try:
        # Resolve every airport before altering road tables, so a missing airport
        # cannot leave the user's database half-cleared.
        node_id_map = _airport_database_ids(cursor, source_nodes)

        cursor.execute("DELETE FROM route_segments")
        cursor.execute("DELETE FROM routes")
        cursor.execute("DELETE FROM roads")
        cursor.execute("DELETE FROM road_types")
        _delete_imported_waypoints(cursor)

        for node in source_nodes.values():
            if not node["is_waypoint"]:
                continue
            cursor.execute(
                "INSERT INTO nodes "
                "(name, lat, lon, is_capital, is_waypoint, region, airport_ident) "
                "VALUES (%s, %s, %s, %s, 1, %s, NULL)",
                (
                    node.get("name"), node["lat"], node["lon"],
                    int(bool(node.get("is_capital", False))), node.get("region"),
                ),
            )
            node_id_map[int(node["id"])] = int(cursor.lastrowid)

        for road_type in data["roadTypes"]:
            cursor.execute(
                "INSERT INTO road_types (id, name, cost_per_step, speed) "
                "VALUES (%s, %s, %s, %s)",
                (
                    road_type["id"], road_type["name"],
                    road_type["cost_per_step"], road_type["speed"],
                ),
            )

        for road_id in sorted(source_roads):
            road = source_roads[road_id]
            cursor.execute(
                "INSERT INTO roads (id, node_a_id, node_b_id, road_type_id, cost) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    road_id, node_id_map[int(road["node_a_id"])],
                    node_id_map[int(road["node_b_id"])],
                    road["road_type_id"], road["cost"],
                ),
            )

        # The JSON intentionally has no route rows. Derive playable directed
        # subroutes from its exact airport-to-airport chains, never new edges.
        # Any pair along the supplied corridor up to six segments away is legal.
        for chain_nodes, chain_roads, route_type in chains:
            for start_index in range(len(chain_nodes) - 1):
                last_end = min(len(chain_nodes), start_index + MAX_ROUTE_HOPS + 1)
                for end_index in range(start_index + 1, last_end):
                    forward_roads = chain_roads[start_index:end_index]
                    cursor.execute(
                        "INSERT INTO routes (start_node_id, end_node_id, road_type_id) "
                        "VALUES (%s, %s, %s)",
                        (
                            node_id_map[chain_nodes[start_index]],
                            node_id_map[chain_nodes[end_index]], route_type,
                        ),
                    )
                    forward_route = int(cursor.lastrowid)
                    cursor.execute(
                        "INSERT INTO routes (start_node_id, end_node_id, road_type_id) "
                        "VALUES (%s, %s, %s)",
                        (
                            node_id_map[chain_nodes[end_index]],
                            node_id_map[chain_nodes[start_index]], route_type,
                        ),
                    )
                    reverse_route = int(cursor.lastrowid)

                    for sequence, road_id in enumerate(forward_roads, start=1):
                        cursor.execute(
                            "INSERT INTO route_segments (route_id, road_id, seq) "
                            "VALUES (%s, %s, %s), (%s, %s, %s)",
                            (
                                forward_route, road_id, sequence,
                                reverse_route, road_id, len(forward_roads) - sequence + 1,
                            ),
                        )

        connection.commit()
        airport_count = sum(
            1 for node in source_nodes.values() if not node["is_waypoint"]
        )
        print(
            f"[MIGRATION 0003] Imported {airport_count} existing airport references "
            f"and {len(source_nodes) - airport_count} JSON-authored waypoints, "
            f"{len(source_roads)} authored roads, and derived routes from "
            f"{len(chains)} supplied airport corridors."
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def apply_seed(connection):
    _seed_network(connection, _load_network())


def rollback_seed(connection):
    data = _load_network()
    source_nodes, _, _ = _node_chains(data)
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM route_segments")
        cursor.execute("DELETE FROM routes")
        cursor.execute("DELETE FROM roads")
        cursor.execute("DELETE FROM road_types")
        _delete_imported_waypoints(cursor)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


steps = [step(apply_seed, rollback_seed)]
