import pygame
import math
from typing import List, Tuple, Optional, Dict, Any


class Road:
    # Centralized style definitions per road type
    STYLES: Dict[str, Dict[str, Any]] = {
        "highway": {"color": (220, 220, 50), "width": 5, "dash": None},
        "main": {"color": (200, 200, 200), "width": 3, "dash": None},
        "dirt": {
            "color": (139, 90, 43),
            "width": 2,
            "dash": (6, 4),
        },  # (dash_len, gap_len)
        "default": {"color": (150, 150, 150), "width": 2, "dash": None},
    }

    def __init__(
        self,
        road_id: str,
        node_a: Any,
        node_b: Any,
        road_type: str = "default",
        cost: float = 1.0,
        offset: float = 0.0,
        curve: float = 0.0,
    ):

        self.id = road_id
        self.node_a = node_a
        self.node_b = node_b
        self.road_type = road_type
        self.cost = cost

        style = self.STYLES.get(road_type, self.STYLES["default"])
        self.color: Tuple[int, int, int] = style["color"]
        self.width: int = style["width"]
        self.dash_pattern: Optional[Tuple[int, int]] = style["dash"]

        self.points: List[Tuple[int, int]] = []
        self.segments: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []

        self._bake_geometry(offset, curve)

    def _bake_geometry(self, offset: float, curve: float):
        ax, ay = self.node_a.pos_x, self.node_a.pos_y
        bx, by = self.node_b.pos_x, self.node_b.pos_y

        if offset != 0:
            dx, dy = bx - ax, by - ay
            length = math.hypot(dx, dy)
            if length > 0:
                px, py = -dy / length, dx / length
                ax += px * offset
                ay += py * offset
                bx += px * offset
                by += py * offset


        num_points = 30
        raw_points: List[Tuple[int, int]] = []

        mid_x, mid_y = (ax + bx) / 2, (ay + by) / 2
        if curve != 0:
            dx, dy = bx - ax, by - ay
            length = math.hypot(dx, dy)
            if length > 0:
                px, py = -dy / length, dx / length
                cx = mid_x + px * curve
                cy = mid_y + py * curve
            else:
                cx, cy = mid_x, mid_y
        else:
            cx, cy = mid_x, mid_y

        for i in range(num_points + 1):
            t = i / num_points
            x = (1 - t) ** 2 * ax + 2 * (1 - t) * t * cx + t**2 * bx
            y = (1 - t) ** 2 * ay + 2 * (1 - t) * t * cy + t**2 * by
            raw_points.append((int(x), int(y)))

        if self.dash_pattern:
            dash_len, gap_len = self.dash_pattern
            self.segments = self._generate_dashed_segments(
                raw_points, float(dash_len), float(gap_len)
            )
        else:
            self.points = raw_points

    @staticmethod
    def _generate_dashed_segments(
        points: List[Tuple[int, int]], dash_len: float, gap_len: float
    ) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        segments: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []
        if not points:
            return segments

        dist_along = 0.0
        drawing = True
        start_pt = points[0]

        for i in range(1, len(points)):
            end_pt = points[i]
            dx = end_pt[0] - start_pt[0]
            dy = end_pt[1] - start_pt[1]
            seg_len = math.hypot(dx, dy)

            if seg_len == 0:
                continue

            remaining = seg_len
            curr_start = start_pt

            while remaining > 0:
                limit = dash_len if drawing else gap_len
                available = limit - dist_along

                if remaining < available:
                    if drawing:
                        segments.append((curr_start, end_pt))
                    dist_along += remaining
                    remaining = 0
                else:
                    ratio = available / remaining
                    break_x = curr_start[0] + dx * ratio
                    break_y = curr_start[1] + dy * ratio
                    break_pt = (int(break_x), int(break_y))

                    if drawing:
                        segments.append((curr_start, break_pt))

                    dist_along = 0.0
                    drawing = not drawing
                    curr_start = break_pt
                    remaining -= available

            start_pt = end_pt

        return segments

    def draw(self, surface: pygame.Surface):
        if self.dash_pattern:
            for p1, p2 in self.segments:
                pygame.draw.line(surface, self.color, p1, p2, self.width)
        else:
            if len(self.points) > 1:
                if self.width <= 1:
                    pygame.draw.aalines(surface, self.color, False, self.points)
                else:
                    pygame.draw.lines(
                        surface, self.color, False, self.points, self.width
                    )

    def get_other_node(self, current_node: Any) -> Any:
        if current_node == self.node_a:
            return self.node_b
        elif current_node == self.node_b:
            return self.node_a
        raise ValueError("Provided node is not an endpoint of this road.")
