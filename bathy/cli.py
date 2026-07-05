"""Command-line entry point."""
from __future__ import annotations

import argparse
import sys

from . import clean, contour, geo, grid, ingest


def cmd_contour(args) -> int:
    soundings = ingest.load(args.log)
    if args.min_depth is not None:
        soundings = [s for s in soundings if s.depth_m >= args.min_depth]
    if args.despike:
        soundings = clean.despike(soundings)
    if not soundings:
        print(f"{args.log}: no soundings after filtering", file=sys.stderr)
        return 2
    _, pts = geo.project_all(soundings)
    g = grid.idw_grid(pts, cell=args.cell)
    contour.plot(g, step=args.step, out=args.out)
    print(f"{len(soundings)} soundings")
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
    c.set_defaults(func=cmd_contour)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
