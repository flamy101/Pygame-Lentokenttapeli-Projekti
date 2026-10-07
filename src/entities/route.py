import pygame
import math
from typing import List, Tuple, Any, Optional

from entities.road import Road


class Route:
    """
    Represents a complete path between a start and end node.
    """

    def __init__(
        self,
        route_id: str,
        start_node: Any,
        end_node: Any,
        road_type: str,
        segments: List[Road],
    ):

        self.id = route_id
        self.start_node = start_node
        self.end_node = end_node
        self.road_type = road_type
        self.segments = segments
        self.hop_count = len(segments)
        self.travel_fare = {"land": 0, "sea": 100, "flight": 300}.get(
            road_type
        )
        self.total_cost = (
            self.travel_fare
            if self.travel_fare is not None
            else sum(road.cost for road in segments)
        )

        self.segment_lengths: List[float] = []
        self.total_distance = 0.0

        self.route_points: List[Tuple[int, int]] = []
        self._bake_route_geometry()

    def _bake_route_geometry(self):
        """Extracts and concatenates points from all segments into one continuous line."""
        for i, road in enumerate(self.segments):
            pts = road.points
            if not pts and road.segments:
                pts = [road.segments[0][0]]
                for _, p2 in road.segments:
                    pts.append(p2)

            if not pts:
                continue

            seg_len = 0.0
            for j in range(1, len(pts)):
                dx = pts[j][0] - pts[j - 1][0]
                dy = pts[j][1] - pts[j - 1][1]
                seg_len += math.hypot(dx, dy)

            self.segment_lengths.append(seg_len)
            self.total_distance += seg_len

            if i == 0:
                self.route_points.extend(pts)
            else:
                self.route_points.extend(pts[1:])

    def get_next_node(self, current_node: Any) -> Optional[Any]:
        """
        Graph traversal: Returns the next node in the route given the current node.
        Returns None if the current node is the end of the route or not in the route.
        """
        if current_node == self.end_node:
            return None

        for i in range(len(self.segments)):
            road = self.segments[i]
            if road.node_a == current_node:
                return road.node_b
            elif road.node_b == current_node:
                return road.node_a

        return None

    def get_node_at_progress(self, progress: float) -> Any:
        """
        Spatial traversal: Returns the node you are currently at (or just passed)
        given a progress value from 0.0 (start) to 1.0 (end) based on total distance.
        """
        if not self.segments:
            return self.start_node

        progress = max(0.0, min(1.0, progress))
        target_dist = progress * self.total_distance

        cumulative_dist = 0.0
        for i, road in enumerate(self.segments):
            cumulative_dist += self.segment_lengths[i]
            if target_dist <= cumulative_dist:
                if progress >= 1.0:
                    return self.end_node
                return road.node_a

        return self.end_node

    def draw(self, surface: pygame.Surface):
        """
        Draws the full path as one continuous polyline across all segments.
        """
        if len(self.route_points) < 2:
            return

        pygame.draw.lines(surface, (0, 80, 180), False, self.route_points, 6)
        pygame.draw.lines(surface, (100, 200, 255), False, self.route_points, 2)
