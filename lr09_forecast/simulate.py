#!/usr/bin/env python3
"""Monte Carlo forecast from a CSV containing sprint velocity."""

from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path


def read_velocity(path: Path, sprint_ids: set[str] | None) -> list[int]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = csv.DictReader(source)
        if not rows.fieldnames or "points_done" not in rows.fieldnames:
            raise ValueError("CSV must contain a points_done column")
        if sprint_ids is not None and "sprint" not in rows.fieldnames:
            raise ValueError("Filtering requires a sprint column")
        values = [
            int(row["points_done"])
            for row in rows
            if sprint_ids is None or row["sprint"] in sprint_ids
        ]
    if not values or any(value < 0 for value in values) or not any(values):
        raise ValueError("Selected velocity must contain non-negative points_done and at least one positive value")
    return values


def percentile(values: list[int], probability: float) -> int:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    interpolated = ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return math.ceil(interpolated - 1e-12)


def forecast(velocity: list[int], remaining: int, runs: int, seed: int) -> tuple[int, int]:
    rng = random.Random(seed)
    durations: list[int] = []
    for _ in range(runs):
        points_left = remaining
        sprints = 0
        while points_left > 0:
            points_left -= rng.choice(velocity)
            sprints += 1
        durations.append(sprints)
    return percentile(durations, 0.50), percentile(durations, 0.85)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--remaining", type=int, required=True)
    parser.add_argument("--runs", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=20261104)
    parser.add_argument(
        "--sprints",
        help="Optional comma-separated sprint IDs to include, for example 1,2",
    )
    args = parser.parse_args()
    if args.remaining <= 0 or args.runs < 1_000:
        parser.error("--remaining must be positive and --runs must be at least 1000")

    selected = set(args.sprints.split(",")) if args.sprints else None
    velocity = read_velocity(args.csv_path, selected)
    p50, p85 = forecast(velocity, args.remaining, args.runs, args.seed)
    print(f"velocity={velocity}")
    print(f"remaining_points={args.remaining}; simulations={args.runs}; seed={args.seed}")
    print(f"P50={p50}; P85={p85}; interval_width={p85 - p50}")


if __name__ == "__main__":
    main()
