import events
from ui import UIElement
import game_events

class Scene:
    """
    Scene superclass.
    """

    def __init__(self, ev_manager, ui_manager, assets):
        self.ev_manager = ev_manager
        self.ui_manager = ui_manager
        self.assets = assets
        self.elements: list[UIElement] = []

    def add(self, element: UIElement) -> UIElement:
        self.elements.append(element)
        return element

    def enter(self):
        self.elements.sort(key=lambda e: e.z_index)
        for e in self.elements:
            self.ui_manager.add(e)

    def exit(self):
        for e in self.elements:
            self.ui_manager.remove(e)

    def draw(self, screen):
        for element in self.elements:
            element.draw(screen)
        self.ui_manager.draw_modal(screen)


class SceneManager:
    """
    Scene manager class.
    Handles scene initialization
    """

    def __init__(self, ev_manager):
        self.ev_manager = ev_manager
        self.scenes: dict[str, Scene] = {}
        self.current: Scene | None = None
        ev_manager.register_listener(self)


    def register(self, name: str, scene: Scene):
        self.scenes[name] = scene

        """
        :param name: Scene name, for example "main"
        :param scene: Scene object
        """

        self.scenes[name] = scene


    def unregister(self, name: str):
        del self.scenes[name]


    def change_to(self, name: str):
        if self.current is not None:
            self.current.exit()
        self.current = self.scenes[name]
        self.current.enter()


    def notify(self, event):
        match event:
            case events.AssetsReadyEvent():
                self.change_to("menu")
            case game_events.ChangeSceneEvent(scene_name=name):
                self.change_to(name)
