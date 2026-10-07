import pygame

from entities.map_node import Node


def make_node(*, is_waypoint=False, name="Helsinki"):
    return Node(
        node_id="node-1",
        name=name,
        lat=60.1699,
        lon=24.9384,
        projector=lambda lat, lon: (100, 100),
        is_waypoint=is_waypoint,
        radius=10,
    )


def test_city_hit_test():
    node = make_node()
    assert node.hit_test((100, 100))
    assert not node.hit_test((200, 200))


def test_waypoint_is_not_clickable():
    node = make_node(is_waypoint=True, name=None)
    assert not node.hit_test((100, 100))


def test_projected_position():
    node = make_node()
    assert (node.pos_x, node.pos_y) == (100, 100)


def test_node_draws():
    pygame.init()
    try:
        make_node().draw(pygame.Surface((800, 600)))
    finally:
        pygame.quit()


def test_highlight_draws():
    pygame.init()
    try:
        node = make_node()
        node.set_highlighted(True)
        node.draw(pygame.Surface((800, 600)))
    finally:
        pygame.quit()
