from os import getenv
from pathlib import Path

import yoyo
from dotenv import load_dotenv

import events


class YoyoConnection:
    def __init__(self, ev_manager):
        self.ev_manager = ev_manager
        self.ev_manager.register_listener(self)

        self.backend = None
        self.migrations = []

    def notify(self, event):
        match event:
            case events.DBConnect(True):
                self.connect()

    def connect(self):
        """
        Create the Yoyo backend and load the migration files.

        """

        project_root = Path(__file__).resolve().parents[2]
        migrations_dir = project_root / "migrations"
        env_file = project_root / ".env"

        load_dotenv(env_file)

        print(f"Reading migrations from: {migrations_dir}")

        try:
            if not migrations_dir.is_dir():
                raise FileNotFoundError(
                    f"Migration directory does not exist: {migrations_dir}"
                )

            host = getenv("DB_HOST")
            port = getenv("DB_PORT")
            user = getenv("DB_USER")
            password = getenv("DB_PASSWORD")
            database = getenv("DB_NAME")

            missing = [
                name
                for name, value in {
                    "DB_HOST": host,
                    "DB_PORT": port,
                    "DB_USER": user,
                    "DB_PASSWORD": password,
                    "DB_NAME": database,
                }.items()
                if value is None
            ]

            if missing:
                raise RuntimeError(
                    f"Missing database environment variables: {', '.join(missing)}"
                )

            database_url = (
                f"mysql://{user}:{password}@{host}:{port}/{database}"
            )

            self.backend = yoyo.get_backend(database_url)
            self.migrations = yoyo.read_migrations(str(migrations_dir))

            print(
                f"Loaded {len(self.migrations)} migration(s): "
                f"{[migration.id for migration in self.migrations]}"
            )

            self.ev_manager.post(
                events.yoyoIsConnected(True)
            )

        except Exception as error:
            print(f"Yoyo database operation failed: {error}")

            self.backend = None
            self.migrations = []

            self.ev_manager.post(
                events.yoyoIsConnected(False)
            )

