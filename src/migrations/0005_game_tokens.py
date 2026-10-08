"""Add per-game token ownership and seed the game's token types."""

from yoyo import step


__depends__ = {"0004_seed_token_types"}
# MariaDB ALTER TABLE implicitly commits. Disable Yoyo's savepoint wrapper so
# an implicit commit cannot make the next step fail with "SAVEPOINT ... does not exist".
__transactional__ = False


TOKEN_TYPES = [
    ("Star of Africa", "reward", 0, 1, "merkki-bitcoin-lvl3"),
    ("200 Iq Haalarimerkki lv3", "reward", 1000, 2, "merkki-200-iq-lv2"),
    ("200 Iq Haalarimerkki lv2", "reward", 600, 3, "merkki-200-iq-lv2"),
    ("Varoitus Haalarimerkki lv1", "reward", 300, 4, "merkki-varoitus-lv1"),
    ("Bandit", "hazard", 0, 3, "merkki-special-bandit"),
    ("Horseshoe", "neutral", 0, 5, "merkki-special-horseshoe"),
    ("Empty", "neutral", 0, 12, "token-empty"),
]

LEGACY_TOKEN_TYPES = [
    ("Afrikan TÃ¤hti", "reward", 5000, 1, "merkki-bitcoin-lvl3"),
    ("Level 2 Reward", "reward", 500, 4, "merkki-200-iq-lv2"),
    ("Level 1 Reward", "reward", 300, 8, "merkki-varoitus-lv1"),
    ("Bandit", "hazard", 0, 5, "merkki-special-bandit"),
    ("Horseshoe", "neutral", 0, 12, "merkki-special-horseshoe"),
]


def _schema_object_exists(cursor, query, params):
    cursor.execute(query, params)
    row = cursor.fetchone()
    value = row[0] if not isinstance(row, dict) else next(iter(row.values()))
    return bool(value)


def _column_exists(cursor, column_name):
    return _schema_object_exists(
        cursor,
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'node_tokens' "
        "AND COLUMN_NAME = %s",
        (column_name,),
    )


def _constraint_exists(cursor, constraint_name):
    return _schema_object_exists(
        cursor,
        "SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS "
        "WHERE CONSTRAINT_SCHEMA = DATABASE() AND TABLE_NAME = 'node_tokens' "
        "AND CONSTRAINT_NAME = %s",
        (constraint_name,),
    )


def _index_exists(cursor, index_name):
    return _schema_object_exists(
        cursor,
        "SELECT COUNT(*) FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'node_tokens' "
        "AND INDEX_NAME = %s",
        (index_name,),
    )


def _seed_types(cursor, token_types):
    cursor.execute("DELETE FROM token_types")
    cursor.executemany(
        "INSERT INTO token_types (name, category, money_delta, weight, texture_key) "
        "VALUES (%s, %s, %s, %s, %s)",
        token_types,
    )


def apply_game_tokens(connection):
    cursor = connection.cursor()
    try:
        # Preserve the migration's original reset behavior. These are the token
        # tables this migration owns; the road and airport tables are untouched.
        cursor.execute("DELETE FROM node_tokens")

        if not _column_exists(cursor, "game_id"):
            cursor.execute("ALTER TABLE node_tokens ADD COLUMN game_id int NULL")
        if not _constraint_exists(cursor, "node_tokens_game_fk"):
            cursor.execute(
                "ALTER TABLE node_tokens ADD CONSTRAINT node_tokens_game_fk "
                "FOREIGN KEY (game_id) REFERENCES games (id)"
            )
        if not _index_exists(cursor, "idx_node_tokens_game_node"):
            cursor.execute(
                "CREATE INDEX idx_node_tokens_game_node "
                "ON node_tokens (game_id, node_id)"
            )

        _seed_types(cursor, TOKEN_TYPES)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def rollback_game_tokens(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM node_tokens")
        if _index_exists(cursor, "idx_node_tokens_game_node"):
            cursor.execute("DROP INDEX idx_node_tokens_game_node ON node_tokens")
        if _constraint_exists(cursor, "node_tokens_game_fk"):
            cursor.execute(
                "ALTER TABLE node_tokens DROP FOREIGN KEY node_tokens_game_fk"
            )
        if _column_exists(cursor, "game_id"):
            cursor.execute("ALTER TABLE node_tokens DROP COLUMN game_id")

        _seed_types(cursor, LEGACY_TOKEN_TYPES)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


steps = [step(apply_game_tokens, rollback_game_tokens)]
