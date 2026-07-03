"""Command-line entry point."""
from __future__ import annotations

import argparse
import sys

from . import contour, geo, grid, ingest


def cmd_contour(args) -> int:
    soundings = ingest.load(args.log)
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
    c.set_defaults(func=cmd_contour)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
