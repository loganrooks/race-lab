#!/usr/bin/env python3
"""Build and validate the Spa circuit reference model from independent sources.

Sources:
- TUMFTM/racetrack-database tracks/Spa.csv: centreline and measured widths.
- TUMFTM/racetrack-database racelines/Spa.csv: minimum-curvature raceline.
- MultiViewer circuit endpoint: independently authored corner marker positions.

The output is deliberately compact enough for a static browser application while
retaining metric coordinates and source provenance.
"""
from __future__ import annotations

import csv
import io
import json
import math
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

TRACK_URL = "https://raw.githubusercontent.com/TUMFTM/racetrack-database/master/tracks/Spa.csv"
RACELINE_URL = "https://raw.githubusercontent.com/TUMFTM/racetrack-database/master/racelines/Spa.csv"
CORNERS_URL = "https://api.multiviewer.app/api/v1/circuits/7/2025"
OUT_DIR = Path(os.environ.get("SPA_REFERENCE_OUT", "spa-race-lab/data/reference"))
SAMPLE_COUNT = 900
OFFICIAL_LENGTH_M = 7004.0


@dataclass(frozen=True)
class TrackPoint:
    x: float
    y: float
    right: float
    left: float


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "SpaRaceLab/2.0"})
    with urllib.request.urlopen(request, timeout=45) as response:  # nosec B310
        return response.read().decode("utf-8")


def parse_track(text: str) -> list[TrackPoint]:
    lines = [line for line in text.splitlines() if line.strip()]
    header = [part.strip() for part in lines[0].lstrip("# ").split(",")]
    rows = csv.DictReader(lines[1:], fieldnames=header)
    return [
        TrackPoint(
            x=float(row["x_m"]),
            y=float(row["y_m"]),
            right=float(row["w_tr_right_m"]),
            left=float(row["w_tr_left_m"]),
        )
        for row in rows
    ]


def parse_xy(text: str) -> np.ndarray:
    lines = [line for line in text.splitlines() if line.strip()]
    header = [part.strip() for part in lines[0].lstrip("# ").split(",")]
    rows = csv.DictReader(lines[1:], fieldnames=header)
    return np.asarray([(float(row["x_m"]), float(row["y_m"])) for row in rows], dtype=float)


def close_loop(points: np.ndarray) -> np.ndarray:
    if np.linalg.norm(points[0] - points[-1]) > 1e-6:
        return np.vstack([points, points[0]])
    return points


def cumulative_distance(points: np.ndarray) -> np.ndarray:
    deltas = np.diff(points, axis=0)
    return np.concatenate([[0.0], np.cumsum(np.linalg.norm(deltas, axis=1))])


def resample_closed(points: np.ndarray, count: int) -> tuple[np.ndarray, np.ndarray]:
    closed = close_loop(points)
    distance = cumulative_distance(closed)
    target = np.linspace(0.0, distance[-1], count, endpoint=False)
    x = np.interp(target, distance, closed[:, 0])
    y = np.interp(target, distance, closed[:, 1])
    return np.column_stack([x, y]), target


def resample_scalar(points: np.ndarray, values: np.ndarray, target_distance: np.ndarray) -> np.ndarray:
    closed = close_loop(points)
    distance = cumulative_distance(closed)
    values_closed = np.concatenate([values, values[:1]]) if len(values) == len(points) else values
    return np.interp(target_distance, distance, values_closed)


def signed_area(points: np.ndarray) -> float:
    nxt = np.roll(points, -1, axis=0)
    return 0.5 * float(np.sum(points[:, 0] * nxt[:, 1] - nxt[:, 0] * points[:, 1]))


def unit_normals(points: np.ndarray) -> np.ndarray:
    tangent = np.roll(points, -1, axis=0) - np.roll(points, 1, axis=0)
    magnitude = np.linalg.norm(tangent, axis=1)
    magnitude[magnitude == 0] = 1.0
    tangent /= magnitude[:, None]
    # Left normal for traversal direction.
    return np.column_stack([-tangent[:, 1], tangent[:, 0]])


def align_raceline(track: np.ndarray, race: np.ndarray) -> tuple[np.ndarray, dict]:
    """Align raceline cyclic origin and direction to the centreline.

    The two TUM files already share scale and coordinates. We only choose the
    cyclic shift/direction that minimizes nearest-index squared error.
    """
    race_resampled, _ = resample_closed(race, len(track))
    best: tuple[float, bool, int, np.ndarray] | None = None
    step = max(1, len(track) // 300)
    track_probe = track[::step]
    for reversed_order in (False, True):
        candidate = race_resampled[::-1] if reversed_order else race_resampled
        for shift in range(0, len(track), step):
            rolled = np.roll(candidate, shift, axis=0)
            score = float(np.mean(np.sum((rolled[::step] - track_probe) ** 2, axis=1)))
            if best is None or score < best[0]:
                best = (score, reversed_order, shift, rolled)
    assert best is not None
    return best[3], {"reversed": best[1], "shift": best[2], "rms_m": math.sqrt(best[0])}


def lateral_coordinates(
    track: np.ndarray,
    normals: np.ndarray,
    race: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    # Same-progress projection is valid after alignment and equal-distance sampling.
    delta = race - track
    lateral = np.sum(delta * normals, axis=1)
    longitudinal = np.sum(delta * np.column_stack([normals[:, 1], -normals[:, 0]]), axis=1)
    return lateral, longitudinal


def similarity_fit(source: np.ndarray, target: np.ndarray, allow_reflection: bool = True):
    source_mean = source.mean(axis=0)
    target_mean = target.mean(axis=0)
    source_centered = source - source_mean
    target_centered = target - target_mean
    covariance = source_centered.T @ target_centered
    u, singular, vt = np.linalg.svd(covariance)
    rotation = vt.T @ u.T
    if not allow_reflection and np.linalg.det(rotation) < 0:
        vt[-1] *= -1
        rotation = vt.T @ u.T
    denominator = float(np.sum(source_centered**2)) or 1.0
    scale = float(np.sum(singular) / denominator)
    translation = target_mean - scale * (source_mean @ rotation)
    transformed = scale * (source @ rotation) + translation
    return transformed, scale, rotation, translation


def nearest_indices(points: np.ndarray, reference: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    distances = np.sum((points[:, None, :] - reference[None, :, :]) ** 2, axis=2)
    indices = np.argmin(distances, axis=1)
    errors = np.sqrt(distances[np.arange(len(points)), indices])
    return indices, errors


def align_corner_markers(raw_corners: list[dict], track: np.ndarray) -> tuple[list[dict], dict]:
    source = np.asarray(
        [[float(c["trackPosition"]["x"]), float(c["trackPosition"]["y"])] for c in raw_corners],
        dtype=float,
    )
    # ICP with multiple coarse initial axis/reflection hypotheses.
    target_center = track.mean(axis=0)
    source_center = source.mean(axis=0)
    source_scale = np.sqrt(np.mean(np.sum((source - source_center) ** 2, axis=1))) or 1.0
    target_scale = np.sqrt(np.mean(np.sum((track - target_center) ** 2, axis=1))) or 1.0
    base = (source - source_center) * (target_scale / source_scale)
    transforms = [
        np.array([[1, 0], [0, 1]], float),
        np.array([[0, -1], [1, 0]], float),
        np.array([[-1, 0], [0, -1]], float),
        np.array([[0, 1], [-1, 0]], float),
        np.array([[-1, 0], [0, 1]], float),
        np.array([[1, 0], [0, -1]], float),
        np.array([[0, 1], [1, 0]], float),
        np.array([[0, -1], [-1, 0]], float),
    ]
    best = None
    for initial in transforms:
        current = base @ initial + target_center
        for _ in range(30):
            idx, _ = nearest_indices(current, track)
            current, scale, rotation, translation = similarity_fit(source, track[idx], allow_reflection=True)
        idx, errors = nearest_indices(current, track)
        score = float(np.sqrt(np.mean(errors**2)))
        if best is None or score < best[0]:
            best = (score, current, idx, errors, scale, rotation, translation)
    assert best is not None
    _, transformed, indices, errors, scale, rotation, translation = best

    # Corner numbers are already in lap order. Unwrap projected indices and find
    # the cyclic track origin that gives the smallest monotonicity penalty.
    progress = indices.astype(float) / len(track)
    unwrapped = progress.copy()
    for i in range(1, len(unwrapped)):
        while unwrapped[i] <= unwrapped[i - 1]:
            unwrapped[i] += 1.0
    progress = np.mod(unwrapped, 1.0)

    corners = []
    for raw, xy, index, error, p in zip(raw_corners, transformed, indices, errors, progress):
        corners.append(
            {
                "turn": int(raw.get("number", 0)),
                "letter": str(raw.get("letter", "")),
                "angleDeg": float(raw.get("angle", 0.0)),
                "progress": round(float(p), 7),
                "trackIndex": int(index),
                "xM": round(float(track[index, 0]), 4),
                "yM": round(float(track[index, 1]), 4),
                "sourceFitErrorM": round(float(error), 3),
            }
        )
    fit = {
        "rmsErrorM": round(float(np.sqrt(np.mean(errors**2))), 3),
        "maxErrorM": round(float(np.max(errors)), 3),
        "scale": float(scale),
        "rotation": rotation.tolist(),
        "translation": translation.tolist(),
    }
    return corners, fit


def curvature(points: np.ndarray) -> np.ndarray:
    prev = np.roll(points, 1, axis=0)
    nxt = np.roll(points, -1, axis=0)
    a = points - prev
    b = nxt - points
    cross = a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
    denom = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1) * np.linalg.norm(nxt - prev, axis=1)
    denom[denom < 1e-9] = np.inf
    return 2.0 * cross / denom


def compact_points(points: np.ndarray, digits: int = 3) -> list[list[float]]:
    return [[round(float(x), digits), round(float(y), digits)] for x, y in points]


def validate(model: dict) -> list[str]:
    failures: list[str] = []
    metrics = model["validation"]
    if not (0.98 * OFFICIAL_LENGTH_M <= metrics["centerlineLengthM"] <= 1.02 * OFFICIAL_LENGTH_M):
        failures.append(f"centreline length {metrics['centerlineLengthM']:.1f} m is not within 2% of 7004 m")
    if metrics["minWidthM"] < 3.0 or metrics["maxWidthM"] > 22.0:
        failures.append(f"width range {metrics['minWidthM']:.2f}–{metrics['maxWidthM']:.2f} m is implausible")
    if metrics["racelineInsideFraction"] < 0.995:
        failures.append(f"only {metrics['racelineInsideFraction']:.3%} of raceline is inside measured boundaries")
    if metrics["racelineMinMarginM"] < -0.25:
        failures.append(f"raceline leaves measured track by {-metrics['racelineMinMarginM']:.2f} m")
    corners = model.get("corners", [])
    if len(corners) != 19:
        failures.append(f"expected 19 independent corner markers, got {len(corners)}")
    turns = [c["turn"] for c in corners]
    if turns != list(range(1, 20)):
        failures.append(f"corner numbering/order is not 1–19: {turns}")
    if model["sources"]["cornerMarkers"]["fit"]["rmsErrorM"] > 35.0:
        failures.append("corner-marker similarity fit exceeds 35 m RMS")
    return failures


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    track_text = fetch_text(TRACK_URL)
    race_text = fetch_text(RACELINE_URL)
    corners_payload = json.loads(fetch_text(CORNERS_URL))

    raw_track = parse_track(track_text)
    track_xy_raw = np.asarray([(p.x, p.y) for p in raw_track], dtype=float)
    left_raw = np.asarray([p.left for p in raw_track], dtype=float)
    right_raw = np.asarray([p.right for p in raw_track], dtype=float)

    track, target_distance = resample_closed(track_xy_raw, SAMPLE_COUNT)
    left = resample_scalar(track_xy_raw, left_raw, target_distance)
    right = resample_scalar(track_xy_raw, right_raw, target_distance)
    race_raw = parse_xy(race_text)
    race, alignment = align_raceline(track, race_raw)

    normals = unit_normals(track)
    left_boundary = track + normals * left[:, None]
    right_boundary = track - normals * right[:, None]
    lateral, longitudinal = lateral_coordinates(track, normals, race)
    margin_left = left - lateral
    margin_right = right + lateral
    margin = np.minimum(margin_left, margin_right)
    inside = (margin_left >= -0.25) & (margin_right >= -0.25)

    raw_corners = corners_payload.get("corners") or []
    raw_corners = sorted(raw_corners, key=lambda item: (int(item.get("number", 0)), str(item.get("letter", ""))))
    corners, marker_fit = align_corner_markers(raw_corners, track)

    centerline_length = float(cumulative_distance(close_loop(track))[-1])
    race_length = float(cumulative_distance(close_loop(race))[-1])
    widths = left + right
    curv = curvature(race)

    model = {
        "schemaVersion": 2,
        "circuit": {
            "name": "Circuit de Spa-Francorchamps",
            "lengthM": OFFICIAL_LENGTH_M,
            "direction": "clockwise" if signed_area(track) < 0 else "counter-clockwise",
            "sampleCount": SAMPLE_COUNT,
        },
        "geometry": {
            "centerlineM": compact_points(track),
            "leftBoundaryM": compact_points(left_boundary),
            "rightBoundaryM": compact_points(right_boundary),
            "leftWidthM": [round(float(v), 3) for v in left],
            "rightWidthM": [round(float(v), 3) for v in right],
            "racelineM": compact_points(race),
            "racelineLateralM": [round(float(v), 3) for v in lateral],
            "racelineCurvature": [round(float(v), 7) for v in curv],
        },
        "corners": corners,
        "validation": {
            "centerlineLengthM": round(centerline_length, 3),
            "racelineLengthM": round(race_length, 3),
            "minWidthM": round(float(np.min(widths)), 3),
            "maxWidthM": round(float(np.max(widths)), 3),
            "meanWidthM": round(float(np.mean(widths)), 3),
            "racelineInsideFraction": round(float(np.mean(inside)), 6),
            "racelineMinMarginM": round(float(np.min(margin)), 3),
            "racelineMeanMarginM": round(float(np.mean(margin)), 3),
            "racelineAlignment": alignment,
            "racelineMaxLongitudinalMisalignmentM": round(float(np.max(np.abs(longitudinal))), 3),
        },
        "sources": {
            "trackGeometry": {
                "url": TRACK_URL,
                "method": "OSM-derived smoothed centreline; widths extracted from satellite imagery by TUMFTM",
                "license": "LGPL-3.0",
            },
            "raceline": {
                "url": RACELINE_URL,
                "method": "TUMFTM minimum-curvature optimization",
                "license": "LGPL-3.0",
            },
            "cornerMarkers": {
                "url": CORNERS_URL,
                "method": "MultiViewer/FastF1 manually authored marker positions, similarity-fitted to TUM geometry",
                "limitations": "FastF1 documents these markers as visualization-grade, not survey-grade.",
                "fit": marker_fit,
            },
        },
    }

    failures = validate(model)
    model["validation"]["failures"] = failures
    (OUT_DIR / "spa-reference.json").write_text(json.dumps(model, separators=(",", ":")), encoding="utf-8")
    report = [
        "# Spa Geometry Validation",
        "",
        f"- Centreline length: {centerline_length:.2f} m (official: {OFFICIAL_LENGTH_M:.0f} m)",
        f"- Measured width range: {np.min(widths):.2f}–{np.max(widths):.2f} m",
        f"- Raceline inside boundaries: {np.mean(inside):.3%}",
        f"- Minimum raceline margin: {np.min(margin):.2f} m",
        f"- Corner marker fit: {marker_fit['rmsErrorM']:.2f} m RMS / {marker_fit['maxErrorM']:.2f} m max",
        "",
        "## Result",
        "",
        "PASS" if not failures else "FAIL",
    ]
    if failures:
        report.extend(["", "## Failures", ""] + [f"- {failure}" for failure in failures])
    (OUT_DIR / "validation-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
