class MapProjector:
    """
    Converts (lat, lon) to Pygame (px, py) coordinates using equirectangular projection.
    Designed to be initialized once at load time and called per node.
    """

    def __init__(
        self, map_bounds: tuple[float, float, float, float], image_size: tuple[int, int]
    ):
        """
        :param map_bounds: (min_lon, min_lat, max_lon, max_lat)
        :param image_size: (width, height) of the map texture in pixels
        """
        self.min_lon, self.min_lat, self.max_lon, self.max_lat = map_bounds
        self.width, self.height = image_size

        self.lon_range = self.max_lon - self.min_lon
        self.lat_range = self.max_lat - self.min_lat

        if self.lon_range == 0 or self.lat_range == 0:
            raise ValueError("Map bounds must have a non-zero width and height.")

    def __call__(self, lat: float, lon: float) -> tuple[int, int]:
        """
        Converts a node's (lat, lon) into map-space (pos_x, pos_y).
        """

        norm_x = (lon - self.min_lon) / self.lon_range
        norm_y = (self.max_lat - lat) / self.lat_range

        
        px_x = round(norm_x * (self.width - 1))
        px_y = round(norm_y * (self.height - 1))

        return px_x, px_y
