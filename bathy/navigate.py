"""Waypoint navigation: steer the boat along a list of (lat, lon) waypoints."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple

_R = 6371000.0  # mean earth radius, metres


def haversine(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * _R * math.asin(min(1.0, math.sqrt(a)))


def bearing(lat1, lon1, lat2, lon2) -> float:
    """Initial bearing from 1 to 2, degrees in [0, 360)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def cross_track(slat, slon, elat, elon, lat, lon) -> float:
    """Signed distance (m) of (lat, lon) from the great-circle line start->end.
    Positive = right of the track direction."""
    d13 = haversine(slat, slon, lat, lon) / _R
    t13 = math.radians(bearing(slat, slon, lat, lon))
    t12 = math.radians(bearing(slat, slon, elat, elon))
    return math.asin(math.sin(d13) * math.sin(t13 - t12)) * _R


@dataclass
class Command:
    throttle: float
    rudder: float
    done: bool = False


@dataclass
class WaypointFollower:
    waypoints: List[Tuple[float, float]]
    arrival_radius: float = 3.0
    kp: float = 0.02      # rudder per degree of heading error
    kx: float = 0.05      # rudder per metre of cross-track error
    cruise: float = 0.6
    _i: int = field(default=0)

    def update(self, lat: float, lon: float, heading: float) -> Command:
        if self._i >= len(self.waypoints):
            return Command(0.0, 0.0, done=True)

        # Advance past every waypoint already within the arrival radius, not just one per
        # update — otherwise coincident/overshot waypoints stall progress for many ticks.
        while (self._i < len(self.waypoints)
               and haversine(lat, lon, *self.waypoints[self._i]) <= self.arrival_radius):
            self._i += 1
        if self._i >= len(self.waypoints):
            return Command(0.0, 0.0, done=True)
        tlat, tlon = self.waypoints[self._i]

        target = bearing(lat, lon, tlat, tlon)
        # Wrap into [-180, 180]; crossing the 0/360 boundary (heading 350, target 010)
        # otherwise gives a ~-340 error and a hard turn the long way round.
        error = (target - heading + 180.0) % 360.0 - 180.0

        # Cross-track correction: steer back toward the line from the previous waypoint.
        xte = 0.0
        if self._i > 0:
            slat, slon = self.waypoints[self._i - 1]
            xte = cross_track(slat, slon, tlat, tlon, lat, lon)

        rudder = max(-1.0, min(1.0, self.kp * error + self.kx * xte))
        return Command(self.cruise, rudder)

    @property
    def index(self) -> int:
        return self._i
