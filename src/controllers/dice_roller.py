"""Event-driven dice rolling with an injected random number generator."""

import random

import game_events


class DiceRoller:
    """Roll an integer from 1 through ``sides`` when requested."""

    def __init__(self, ev_manager, sides: int = 6, *, rng: random.Random):
        if sides < 1:
            raise ValueError("Dice must have at least one side")
        if not isinstance(rng, random.Random):
            raise TypeError("rng must be an injected random.Random instance")

        self.ev_manager = ev_manager
        self.sides = sides
        self.rng = rng
        self.current_value: int | None = None
        ev_manager.register_listener(self)

    def notify(self, event):
        if not isinstance(event, game_events.RollRequestedEvent):
            return

        self.current_value = self.rng.randint(1, self.sides)
        self.ev_manager.post(
            game_events.DiceRolledEvent(
                event.player_id,
                self.current_value,
                event.current_node_id,
            )
        )
