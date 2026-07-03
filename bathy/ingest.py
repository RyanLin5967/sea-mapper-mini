"""Load logged soundings from the Deeper sonar CSV export."""
from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Sounding:
    lat: float
    lon: float
    depth_m: float
    temp_c: Optional[float] = None


_LAT_KEYS = {"latitude", "lat"}
_LON_KEYS = {"longitude", "lon", "lng", "long"}
_DEPTH_KEYS = {"depth", "depth_m", "depth(m)", "depth (m)"}
_TEMP_KEYS = {"temperature", "temp", "temp_c", "water_temp"}


def _pick(header, keys):
    for i, h in enumerate(header):
        if h.strip().lower() in keys:
            return i
    return None


def _sniff_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        # Fall back to whichever common delimiter appears most in the header.
        return max(",;\t", key=sample.splitlines()[0].count) if sample else ","


def load_csv(path: str) -> List[Sounding]:
    out: List[Sounding] = []
    with open(path, newline="") as f:
        delim = _sniff_delimiter(f.read(4096))
        f.seek(0)
        reader = csv.reader(f, delimiter=delim)
        header = next(reader, None)
        if header is None:
            raise ValueError(f"{path}: empty file")
        ilat = _pick(header, _LAT_KEYS)
        ilon = _pick(header, _LON_KEYS)
        idep = _pick(header, _DEPTH_KEYS)
        itmp = _pick(header, _TEMP_KEYS)
        if ilat is None or ilon is None or idep is None:
            raise ValueError(f"{path}: need latitude, longitude, depth columns")
        for row in reader:
            if len(row) <= max(ilat, ilon, idep):
                continue
            try:
                lat = float(row[ilat]); lon = float(row[ilon]); depth = float(row[idep])
            except ValueError:
                continue
            # The sonar logs depth 0.0 when it has no bottom lock; those pings are not
            # real soundings and pull the interpolated surface shallow. Drop them.
            if depth <= 0.0:
                continue
            temp = None
            if itmp is not None and itmp < len(row):
                try:
                    temp = float(row[itmp])
                except ValueError:
                    temp = None
            out.append(Sounding(lat, lon, depth, temp))
    return out


def load_gpx(path: str) -> List[Sounding]:
    """Parse a GPX track; depth comes from a <depth> extension on each point."""
    out: List[Sounding] = []
    root = ET.parse(path).getroot()
    for el in root.iter():  # strip namespaces so tags match plainly
        el.tag = el.tag.rsplit("}", 1)[-1]
    for pt in root.iter("trkpt"):
        try:
            lat = float(pt.attrib["lat"]); lon = float(pt.attrib["lon"])
        except (KeyError, ValueError):
            continue
        d = pt.find(".//depth")
        if d is None or d.text is None:
            continue
        try:
            depth = float(d.text)
        except ValueError:
            continue
        if depth <= 0.0:
            continue
        out.append(Sounding(lat, lon, depth))
    return out


def load(path: str) -> List[Sounding]:
    """Load soundings, dispatching on file extension."""
    if path.lower().endswith(".gpx"):
        return load_gpx(path)
    return load_csv(path)
