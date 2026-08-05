"""Boat links: a serial link to the RC boat, and a simulator for testing."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from .navigate import Command

_R = 6371000.0


class BoatLink:
    def state(self) -> Tuple[float, float, float, Optional[float]]:
        """Return (lat, lon, heading_deg, depth_m or None)."""
        raise NotImplementedError

    def drive(self, cmd: Command) -> None:
        raise NotImplementedError

    def close(self) -> None:
        pass


@dataclass
class SimBoat(BoatLink):
    """Kinematic simulator. `depth_fn(lat, lon) -> metres` supplies synthetic soundings."""
    lat: float
    lon: float
    heading: float = 0.0
    speed_max: float = 1.5
    turn_rate_max: float = 40.0
    dt: float = 0.2
    depth_fn: Optional[Callable[[float, float], float]] = None
    _throttle: float = 0.0
    _rudder: float = 0.0

    def drive(self, cmd: Command) -> None:
        self._throttle = max(0.0, min(1.0, cmd.throttle))
        self._rudder = max(-1.0, min(1.0, cmd.rudder))

    def step(self) -> None:
        self.heading = (self.heading + self._rudder * self.turn_rate_max * self.dt) % 360.0
        d = self._throttle * self.speed_max * self.dt
        dn = d * math.cos(math.radians(self.heading))
        de = d * math.sin(math.radians(self.heading))
        self.lat += math.degrees(dn / _R)
        self.lon += math.degrees(de / (_R * math.cos(math.radians(self.lat))))

    def state(self):
        depth = self.depth_fn(self.lat, self.lon) if self.depth_fn else None
        return self.lat, self.lon, self.heading, depth


class SerialBoat(BoatLink):
    """Talk to the RC boat over serial.

    Commands go out as `D,<throttle>,<rudder>\n`; the boat's firmware emits state lines
    `S,<lat>,<lon>,<heading>,<depth>`.
    """

    def __init__(self, port: str, baud: int = 57600, timeout: float = 1.0):
        import serial  # pyserial
        self._ser = serial.Serial(port, baud, timeout=timeout)
        self._last: Tuple[float, float, float, Optional[float]] = (0.0, 0.0, 0.0, None)

    def drive(self, cmd: Command) -> None:
        self._ser.write(f"D,{cmd.throttle:.3f},{cmd.rudder:.3f}\n".encode("ascii"))

    def state(self):
        raw = self._ser.readline().decode("ascii", "ignore").strip()
        if raw.startswith("S,"):
            parts = raw.split(",")
            try:
                lat = float(parts[1]); lon = float(parts[2]); hdg = float(parts[3])
                depth = float(parts[4]) if len(parts) > 4 and parts[4] else None
                self._last = (lat, lon, hdg, depth)
            except (ValueError, IndexError):
                pass
        return self._last

    def close(self) -> None:
        try:
            self.drive(Command(0.0, 0.0))
        finally:
            self._ser.close()
