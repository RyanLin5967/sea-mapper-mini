"""Command-line entry point."""
from __future__ import annotations

import argparse
import sys

import math

from . import clean, contour, geo, grid, ingest, mission, survey


def cmd_contour(args) -> int:
    soundings = ingest.load(args.log)
    if args.min_depth is not None:
        soundings = [s for s in soundings if s.depth_m >= args.min_depth]
    if args.despike:
        soundings = clean.despike(soundings)
    if not soundings:
        print(f"{args.log}: no soundings after filtering", file=sys.stderr)
        return 2
    ref, pts = geo.project_all(soundings)
    g = grid.idw_grid(pts, cell=args.cell)
    xy = [(x, y) for x, y, _ in pts]
    contour.plot(g, step=args.step, out=args.out, soundings_xy=xy)
    if args.geojson:
        contour.to_geojson(g, args.step, geo.unprojector(*ref), args.geojson)
        print(f'wrote {args.geojson}')
    print(f"{len(soundings)} soundings")
    return 0


def _corner(s):
    lat, lon = (float(v) for v in s.split(","))
    return lat, lon


def cmd_survey(args) -> int:
    wps = survey.plan_latlon(_corner(args.corner_a), _corner(args.corner_b), spacing=args.spacing)
    print(f"{len(wps)} waypoints, {len(wps)//2} lines, {args.spacing} m spacing")
    for lat, lon in wps:
        print(f"{lat:.6f},{lon:.6f}")
    return 0


def cmd_run(args) -> int:
    wps = survey.plan_latlon(_corner(args.corner_a), _corner(args.corner_b), spacing=args.spacing)
    a, b = _corner(args.corner_a), _corner(args.corner_b)
    clat, clon = (a[0]+b[0])/2, (a[1]+b[1])/2
    if args.sim:
        def depth_fn(lat, lon):
            dn = (lat-clat)*111000.0
            de = (lon-clon)*111000.0*math.cos(math.radians(clat))
            return max(0.3, 10.0 - 0.0005*(dn*dn+de*de))
        from .boat import SimBoat
        boat = SimBoat(lat=wps[0][0], lon=wps[0][1], depth_fn=depth_fn)
    else:
        from .boat import SerialBoat
        boat = SerialBoat(args.port, baud=args.baud)
    n = mission.run_mission(boat, wps, out_csv=args.out, arrival_radius=args.arrival)
    print(f"logged {n} soundings to {args.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="bathy")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("contour", help="build a contour map from a sonar log")
    c.add_argument("log")
    c.add_argument("--out")
    c.add_argument("--step", type=float, default=1.0)
    c.add_argument("--cell", type=float, default=2.0)
    c.add_argument("--despike", action="store_true", help="median-despike the track")
    c.add_argument("--min-depth", type=float, default=None, help="drop depths below this (m)")
    c.add_argument("--geojson", help="also export contour lines as GeoJSON")
    c.set_defaults(func=cmd_contour)

    s = sub.add_parser("survey", help="plan survey lines over a rectangle")
    s.add_argument("corner_a"); s.add_argument("corner_b")
    s.add_argument("--spacing", type=float, default=10.0)
    s.set_defaults(func=cmd_survey)

    r = sub.add_parser("run", help="run an autonomous survey, logging soundings")
    r.add_argument("corner_a"); r.add_argument("corner_b")
    r.add_argument("--spacing", type=float, default=10.0)
    r.add_argument("--arrival", type=float, default=3.0)
    r.add_argument("--out", default="mission_log.csv")
    r.add_argument("--sim", action="store_true")
    r.add_argument("--port"); r.add_argument("--baud", type=int, default=57600)
    r.set_defaults(func=cmd_run)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
