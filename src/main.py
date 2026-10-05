import pygame
from scenes.gameplay_scene import GameScene
from scenes.menu_scene import MenuScene
from scenes.rules_scene import RulesScene
from music import Music
from assets import Assets
from models.db.db_connector import DBConnector
from models.yoyo.yoyo_connection import yoyoConnection
from models.yoyo.yoyo_opirations import yoyoOperations

import ui
import scenes
import controller
import eventmanager
import model
import view


def main():

    ev_manager = eventmanager.EventManager()

    assets = Assets(ev_manager)
    game_model = model.Engine(ev_manager)
    ui_manager = ui.UIManager(ev_manager)
    scene_manager = scenes.SceneManager(ev_manager)
    scene_manager.register("rules", RulesScene(ev_manager, ui_manager, assets))
    graphics = view.Graphics(ev_manager, game_model, scene_manager)
    keyboard = controller.Keyboard(ev_manager, game_model)
    db_connector = DBConnector(ev_manager)
    music = Music(assets, ev_manager)

    yoyo_connection = yoyoConnection(ev_manager)
    yoyo_opirations = yoyoOperations(ev_manager, yoyo_connection)

    scene_manager.register("menu", MenuScene(ev_manager, ui_manager, assets))
    scene_manager.register("game", GameScene(ev_manager, ui_manager, assets))

    game_model.run()
    
    game_id = db_connector.create_new_game()
    print(game_id)

if __name__ == "__main__":
    main()
