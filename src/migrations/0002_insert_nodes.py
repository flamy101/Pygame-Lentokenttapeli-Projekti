from yoyo import step


__transactional__ = True

steps = [
    step(
        """
        INSERT INTO nodes (name, lat, lon, is_capital, is_waypoint, region, airport_ident)
        SELECT
            name,
            latitude_deg,
            longitude_deg,
            0 AS is_capital,
            0 AS is_waypoint,
            municipality AS iso_region,
            ident AS airport_ident
        FROM airport
        WHERE continent = 'AF'
          AND type IN ('large_airport')
          AND type != 'closed'
          and longitude_deg < 50
          AND ident NOT IN (
              'HEGN', 'HTZA', 'HTDA', 'TN-0002', 'FDSK', 'HUEN', 'GBYD', 'GOBD',
              'FAOR', 'GQNO', 'DGAA', 'DNAA', 'HKJK', 'FQMA', 'FZAA', 'HESH', 'DNMM', 'FKKD', 'FAOR', 'DTTA', 'HRYR'
          );
        """
    )
]