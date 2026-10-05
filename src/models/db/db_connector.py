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
        self.connection = None


    def notify(self, event):
        match event:
            case events.PygameReadyEvent():
                print("Checking for connection...")
                self.is_connected()
                
            


    def is_connected(self):
        if getenv("DEBUG") == "TRUE":
            return

        try:
            self.connection = mariadb.connect(
                host = getenv("DB_HOST"),
                port = int(getenv("DB_PORT")),
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


