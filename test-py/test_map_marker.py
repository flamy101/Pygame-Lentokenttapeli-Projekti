import os
import sys

import pygame

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from src.map_marker import Node


def test_city_hit_test():
    node = Node(
        id=1,
        name="Helsinki",
        lat=60.1699,
        lon=24.9384,
        radius=10,
    )

    node.set_projected_position(100, 100)

    assert node.hit_test((100, 100))
    assert not node.hit_test((200, 200))


def test_waypoint_is_not_clickable():
    node = Node(
        id=2,
        name=None,
        lat=60.0,
        lon=25.0,
        is_waypoint=True,
    )

    node.set_projected_position(100, 100)

    assert not node.hit_test((100, 100))


def test_projected_position():
    node = Node(
        id=1,
        name="Helsinki",
        lat=60.0,
        lon=25.0,
    )

    node.set_projected_position(500, 300)

    assert node.pos_x == 500
    assert node.pos_y == 300
    assert node.position == (500, 300)


def test_node_draws():
    pygame.init()

    screen = pygame.Surface((800, 600))

    node = Node(
        id=1,
        name="Helsinki",
        lat=60.0,
        lon=25.0,
        radius=6,
        color=(255, 255, 255),
    )

    node.set_projected_position(400, 300)
    node.draw(screen)

    pygame.quit()


def test_highlight_draws():
    pygame.init()

    screen = pygame.Surface((800, 600))

    node = Node(
        id=1,
        name="Helsinki",
        lat=60.0,
        lon=25.0,
    )

    node.set_projected_position(400, 300)
    node.highlighted = True
    node.draw(screen)

    pygame.quit()


if __name__ == "__main__":
    test_city_hit_test()
    print("✓ city hit test")

    test_waypoint_is_not_clickable()
    print("✓ waypoint is not clickable")

    test_projected_position()
    print("✓ projected position")

    test_node_draws()
    print("✓ city drawing")

    test_highlight_draws()
    print("✓ highlight drawing")

    print("\nAll Node tests passed!")