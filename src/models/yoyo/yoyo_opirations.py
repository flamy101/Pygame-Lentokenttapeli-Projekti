import events


class YoyoOperations:

    def __init__(self, ev_manager, yoyo_connection):
        self.ev_manager = ev_manager
        self.ev_manager.register_listener(self)

        self.yoyo = yoyo_connection

    def notify(self, event):
        match event:
            case events.yoyoIsConnected(True):
                self.apply_migrations()

    def check_migrations(self):
        """
        Get the Yoyo MigrationList containing migrations
        that have not yet been applied.
        """

        pending = self.yoyo.backend.to_apply(
            self.yoyo.migrations
        )

        print(
            f"Pending migrations ({len(pending)}): "
            f"{[migration.id for migration in pending]}"
        )

        self.ev_manager.post(
            events.yoyoCheckMigrations(pending)
        )

        return pending

    def apply_migrations(self):
        """
        Apply all pending migrations using Yoyo's documented API.
        """

        try:
            with self.yoyo.backend.lock():

                pending = self.check_migrations()

                if not pending:
                    print("No pending migrations.")

                    self.ev_manager.post(
                        events.yoyoApplyingMigrations(False)
                    )
                    return

                # IMPORTANT:
                # Do NOT convert `pending` to a normal Python list.
                self.yoyo.backend.apply_migrations(pending)

            print(
                f"Applied {len(pending)} migration(s)"
            )

            self.ev_manager.post(
                events.yoyoApplyingMigrations(True)
            )

        except Exception as error:
            print(
                f"Yoyo migrations failed: {error}"
            )

            self.ev_manager.post(
                events.yoyoApplyingMigrations(False)
            )
