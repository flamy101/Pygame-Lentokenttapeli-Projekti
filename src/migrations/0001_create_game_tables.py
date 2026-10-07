from yoyo import step


__transactional__ = False


steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS country (
            iso_country varchar(40) NOT NULL,
            name varchar(40),
            continent varchar(40),
            wikipedia_link varchar(40),
            keywords varchar(40),
            PRIMARY KEY (iso_country)
        ) CHARACTER SET latin1
        """,
        ""
    ),

    step(
        """
        CREATE TABLE IF NOT EXISTS airport (
            ident varchar(40) NOT NULL,
            type varchar(40),
            name varchar(40),
            latitude_deg double,
            longitude_deg double,
            elevation_ft int,
            continent varchar(40),
            iso_country varchar(40),
            iso_region varchar(40),
            municipality varchar(40),
            scheduled_service varchar(40),
            gps_code varchar(40),
            iata_code varchar(40),
            local_code varchar(40),
            home_link varchar(40),
            wikipedia_link varchar(40),
            keywords varchar(40),
            PRIMARY KEY (ident),
            FOREIGN KEY (iso_country)
                REFERENCES country (iso_country),
            INDEX (iso_country)
        ) CHARACTER SET latin1
        """,
        ""
    ),

    step(
        """
        CREATE TABLE IF NOT EXISTS games (
            id int AUTO_INCREMENT PRIMARY KEY,
            created_at timestamp DEFAULT current_timestamp() NOT NULL,
            current_turn int DEFAULT 0 NOT NULL,
            is_finished tinyint(1) DEFAULT 0 NOT NULL
        ) COLLATE = utf8mb4_unicode_ci
        """,
        ""
    ),

    step(
        """
        CREATE TABLE IF NOT EXISTS game (
            id varchar(40) NOT NULL,
            co2_consumed int DEFAULT 0,
            co2_budget int DEFAULT 0,
            location varchar(40),
            screen_name varchar(40),
            PRIMARY KEY (id),
            FOREIGN KEY (location)
                REFERENCES airport (ident),
            INDEX (location)
        ) CHARACTER SET latin1
        """,
        ""
    ),

    step(
        """
        CREATE TABLE IF NOT EXISTS nodes (
            id int AUTO_INCREMENT PRIMARY KEY,
            name varchar(100),
            lat decimal(9, 6) NOT NULL,
            lon decimal(9, 6) NOT NULL,
            is_capital tinyint(1) DEFAULT 0 NOT NULL,
            is_waypoint tinyint(1) DEFAULT 0 NOT NULL,
            region varchar(50),
            airport_ident varchar(40) CHARACTER SET latin1,
            FOREIGN KEY (airport_ident)
                REFERENCES airport (ident),
            INDEX (airport_ident)
        ) COLLATE = utf8mb4_unicode_ci
        """,
        ""
    ),

    step(
        """
        CREATE TABLE IF NOT EXISTS road_types (
            id int AUTO_INCREMENT PRIMARY KEY,
            name varchar(20) NOT NULL UNIQUE,
            cost_per_step int DEFAULT 0 NOT NULL,
            speed int DEFAULT 1 NOT NULL
        ) COLLATE = utf8mb4_unicode_ci
        """,
        ""
    ),

    step(
        """
        CREATE TABLE IF NOT EXISTS roads (
            id int AUTO_INCREMENT PRIMARY KEY,
            node_a_id int NOT NULL,
            node_b_id int NOT NULL,
            road_type_id int NOT NULL,
            cost int DEFAULT 0 NOT NULL,
            UNIQUE (node_a_id, node_b_id, road_type_id),
            FOREIGN KEY (node_a_id)
                REFERENCES nodes (id),
            FOREIGN KEY (node_b_id)
                REFERENCES nodes (id),
            FOREIGN KEY (road_type_id)
                REFERENCES road_types (id),
            CHECK (node_a_id <> node_b_id),
            INDEX (node_a_id),
            INDEX (node_b_id)
        ) COLLATE = utf8mb4_unicode_ci
        """,
        ""
    ),

    step(
        """
        CREATE TABLE IF NOT EXISTS routes (
            id int AUTO_INCREMENT PRIMARY KEY,
            start_node_id int NOT NULL,
            end_node_id int NOT NULL,
            road_type_id int NOT NULL,
            FOREIGN KEY (start_node_id)
                REFERENCES nodes (id),
            FOREIGN KEY (end_node_id)
                REFERENCES nodes (id),
            FOREIGN KEY (road_type_id)
                REFERENCES road_types (id),
            CHECK (start_node_id <> end_node_id),
            INDEX (start_node_id),
            INDEX (end_node_id)
        ) COLLATE = utf8mb4_unicode_ci
        """,
        ""
    ),

    step(
        """
        CREATE TABLE IF NOT EXISTS players (
            id               int AUTO_INCREMENT PRIMARY KEY,
            game_id          int                  NOT NULL,
            name             varchar(50)          NOT NULL,
            color            varchar(20)          NOT NULL,
            money            int        DEFAULT 0 NOT NULL,
            current_node_id  int                  NOT NULL,
            current_route_id int                  NULL,
            route_progress   int        DEFAULT 0 NOT NULL,
            turn_order       int                  NOT NULL,
            is_eliminated    tinyint(1) DEFAULT 0 NOT NULL,
            has_won          tinyint(1) DEFAULT 0 NOT NULL,
            CONSTRAINT players_game_fk
                FOREIGN KEY (game_id) REFERENCES games (id),
            CONSTRAINT players_node_fk
                FOREIGN KEY (current_node_id) REFERENCES nodes (id),
            CONSTRAINT players_route_fk
                FOREIGN KEY (current_route_id) REFERENCES routes (id),
            INDEX idx_players_game (game_id)
        ) COLLATE = utf8mb4_unicode_ci
        """,
        ""
    ),

    step(
        """
        CREATE TABLE IF NOT EXISTS player_items (
            id int AUTO_INCREMENT PRIMARY KEY,
            player_id int NOT NULL,
            item_name varchar(50) NOT NULL,
            quantity int DEFAULT 1 NOT NULL,
            FOREIGN KEY (player_id)
                REFERENCES players (id),
            INDEX (player_id)
        ) COLLATE = utf8mb4_unicode_ci
        """,
        ""
    ),

    step(
        """
        CREATE TABLE IF NOT EXISTS route_segments (
            id int AUTO_INCREMENT PRIMARY KEY,
            route_id int NOT NULL,
            road_id int NOT NULL,
            seq int NOT NULL,
            UNIQUE (route_id, seq),
            FOREIGN KEY (route_id)
                REFERENCES routes (id),
            FOREIGN KEY (road_id)
                REFERENCES roads (id),
            INDEX (route_id, seq)
        ) COLLATE = utf8mb4_unicode_ci
        """,
        ""
    ),

    step(
        """
        CREATE TABLE IF NOT EXISTS token_types (
            id int AUTO_INCREMENT PRIMARY KEY,
            name varchar(50) NOT NULL UNIQUE,
            category enum('reward', 'hazard', 'neutral') NOT NULL,
            money_delta int DEFAULT 0 NOT NULL,
            weight int DEFAULT 1 NOT NULL,
            texture_key varchar(50) NOT NULL
        ) COLLATE = utf8mb4_unicode_ci
        """,
        ""
    ),

    step(
        """
        CREATE TABLE IF NOT EXISTS node_tokens (
            id int AUTO_INCREMENT PRIMARY KEY,
            node_id int NOT NULL,
            token_type_id int NOT NULL,
            is_claimed tinyint(1) DEFAULT 0 NOT NULL,
            FOREIGN KEY (node_id)
                REFERENCES nodes (id),
            FOREIGN KEY (token_type_id)
                REFERENCES token_types (id),
            INDEX (node_id)
        ) COLLATE = utf8mb4_unicode_ci
        """,
        ""
    ),


]
