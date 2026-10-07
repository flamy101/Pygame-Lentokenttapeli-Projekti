import random

import pygame

import game_events
from controllers.dice_roller import DiceRoller
from eventmanager import EventManager
from ui.elements import Button


class EventRecorder:
    def __init__(self):
        self.events = []

    def notify(self, event):
        self.events.append(event)


def test_roll_button_posts_requests_and_dice_results(capsys):
    ev_manager = EventManager()
    roller = DiceRoller(ev_manager, sides=6, rng=random.Random(417))
    recorder = EventRecorder()
    ev_manager.register_listener(recorder)
    button = Button(
        pygame.Rect(0, 0, 100, 40),
        callback=lambda: ev_manager.post(game_events.RollRequestedEvent("p1")),
    )

    for _ in range(5):
        button.on_click()

    dice_events = [e for e in recorder.events if isinstance(e, game_events.DiceRolledEvent)]
    assert len(dice_events) == 5
    assert all(e.player_id == "p1" and 1 <= e.value <= 6 for e in dice_events)
    assert roller.current_value == dice_events[-1].value

    output = capsys.readouterr().out
    assert "Dice rolled event" in output
    assert all(str(e.value) in output for e in dice_events)


def test_dice_roller_passes_optional_current_node_id():
    ev_manager = EventManager()
    roller = DiceRoller(ev_manager, rng=random.Random(2))
    recorder = EventRecorder()
    ev_manager.register_listener(recorder)

    ev_manager.post(game_events.RollRequestedEvent("p2", "node-7"))

    dice_event = next(e for e in recorder.events if isinstance(e, game_events.DiceRolledEvent))
    assert dice_event.current_node_id == "node-7"
