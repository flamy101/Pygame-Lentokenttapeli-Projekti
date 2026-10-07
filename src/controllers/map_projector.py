class MapProjector:
    """
    Converts (lat, lon) to Pygame (px, py) coordinates using equirectangular projection.
    Designed to be initialized once at load time and called per node.
    """

    def __init__(
        self,
        map_bounds: tuple[float, float, float, float],
        image_size: tuple[int, int],
        offset_y: float = 0.0,
        scale_y: float = 1.0,
    ):
        """
        :param map_bounds: (min_lon, min_lat, max_lon, max_lat)
        :param image_size: (width, height) of the map texture in pixels
        """
        self.min_lon, self.min_lat, self.max_lon, self.max_lat = map_bounds
        self.width, self.height = image_size
        self.offset_y = offset_y
        self.scale_y = scale_y

        self.lon_range = self.max_lon - self.min_lon
        self.lat_range = self.max_lat - self.min_lat

        if self.lon_range == 0 or self.lat_range == 0:
            raise ValueError("Map bounds must have a non-zero width and height.")

        self._georeference_triangles = None

    @classmethod
    def from_control_points(cls, image_size, control_points, scale_y=1.0):
        """Create a projector from NW, NE, SE, SW, and center tie points.

        Control point values are ``(latitude, longitude)`` decimal-degree pairs.
        Four triangles around the center preserve every supplied reference.
        """
        projector = cls((0.0, 0.0, 1.0, 1.0), image_size)
        projector.scale_y = scale_y
        width, height = image_size
        pixel_points = {
            "nw": (0.0, 0.0),
            "ne": (float(width), 0.0),
            "se": (float(width), float(height)),
            "sw": (0.0, float(height)),
            "center": (width / 2, height / 2),
        }
        triangle_names = (
            ("nw", "ne", "center"),
            ("ne", "se", "center"),
            ("se", "sw", "center"),
            ("sw", "nw", "center"),
        )
        projector._georeference_triangles = [
            (
                tuple(
                    (control_points[name][1], control_points[name][0])
                    for name in names
                ),
                tuple(pixel_points[name] for name in names),
            )
            for names in triangle_names
        ]
        return projector

    @staticmethod
    def _barycentric(point, triangle):
        x, y = point
        (x0, y0), (x1, y1), (x2, y2) = triangle
        denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if denominator == 0:
            raise ValueError("Georeference points contain a degenerate triangle.")
        weight0 = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / denominator
        weight1 = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / denominator
        return weight0, weight1, 1.0 - weight0 - weight1

    def _project_control_points(self, lat, lon):
        point = (lon, lat)
        candidates = []
        for geographic, pixels in self._georeference_triangles:
            weights = self._barycentric(point, geographic)
            penalty = sum(max(0.0, -weight) ** 2 for weight in weights)
            candidates.append((penalty, weights, pixels))

        _, weights, pixels = min(candidates, key=lambda candidate: candidate[0])
        x = sum(weight * pixel[0] for weight, pixel in zip(weights, pixels))
        y = sum(weight * pixel[1] for weight, pixel in zip(weights, pixels))
        y = self.height / 2 + (y - self.height / 2) * self.scale_y
        return round(x), round(y)

    def __call__(self, lat: float, lon: float) -> tuple[int, int]:
        """
        Converts a node's (lat, lon) into map-space (pos_x, pos_y).
        """

        if self._georeference_triangles is not None:
            return self._project_control_points(lat, lon)

        norm_x = (lon - self.min_lon) / self.lon_range
        norm_y = (self.max_lat - lat) / self.lat_range

        
        px_x = round(norm_x * (self.width - 1))
        px_y = round(
            self.height / 2
            + (norm_y * (self.height - 1) - self.height / 2) * self.scale_y
            + self.offset_y
        )

        return px_x, px_y
