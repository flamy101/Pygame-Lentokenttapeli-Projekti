import pygame
import math
from typing import List, Tuple, Optional, Dict, Any


class Road:
    # Centralized style definitions per road type
    STYLES: Dict[str, Dict[str, Any]] = {
        "highway": {"color": (220, 220, 50), "width": 5, "dash": None},
        "main": {"color": (200, 200, 200), "width": 3, "dash": None},
        "land": {"color": (245, 218, 105), "width": 42, "dash": None},
        "sea": {"color": (70, 190, 235), "width": 42, "dash": None},
        "flight": {"color": (255, 120, 70), "width": 38, "dash": None},
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
        self.curve = curve
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

    def set_curve(self, curve: float):
        """Rebuild this road with a signed map-space curve offset."""
        self._bake_geometry(0.0, curve)

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
            curr_x, curr_y = float(start_pt[0]), float(start_pt[1])
            remaining = math.hypot(end_pt[0] - curr_x, end_pt[1] - curr_y)

            while remaining > 0:
                limit = dash_len if drawing else gap_len
                available = limit - dist_along
                step = min(remaining, available)
                dx = end_pt[0] - curr_x
                dy = end_pt[1] - curr_y
                ratio = step / remaining
                next_x = curr_x + dx * ratio
                next_y = curr_y + dy * ratio

                if drawing and step > 0:
                    segments.append(
                        ((round(curr_x), round(curr_y)), (round(next_x), round(next_y)))
                    )

                curr_x, curr_y = next_x, next_y
                remaining -= step
                dist_along += step
                if dist_along >= limit:
                    dist_along = 0.0
                    drawing = not drawing

            start_pt = end_pt

        return segments

    def draw(self, surface: pygame.Surface):
        if self.dash_pattern:
            for p1, p2 in self.segments:
                pygame.draw.line(surface, (25, 28, 35), p1, p2, self.width + 10)
                pygame.draw.line(surface, self.color, p1, p2, self.width)
        else:
            if len(self.points) > 1:
                pygame.draw.lines(
                    surface, (25, 28, 35), False, self.points, self.width + 10
                )
                if self.width <= 1:
                    pygame.draw.aalines(surface, self.color, False, self.points)
                else:
                    pygame.draw.lines(
                        surface, self.color, False, self.points, self.width
                    )

        # Roads are stored as short edges between waypoint nodes. pygame's line
        # caps are square, so the dark outline can show through at angled joins.
        # Round both layers at the endpoints so adjacent edges form one stroke.
        if self.width > 1:
            endpoints = (
                (self.segments[0][0], self.segments[-1][1])
                if self.dash_pattern and self.segments
                else (self.points[0], self.points[-1])
                if self.points
                else ()
            )
            for point in endpoints:
                pygame.draw.circle(surface, (25, 28, 35), point, (self.width + 10) // 2)
                pygame.draw.circle(surface, self.color, point, self.width // 2)

    def get_other_node(self, current_node: Any) -> Any:
        if current_node == self.node_a:
            return self.node_b
        elif current_node == self.node_b:
            return self.node_a
        raise ValueError("Provided node is not an endpoint of this road.")
