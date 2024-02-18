import logging
import json
import os
import subprocess
from typing import Dict, List, TypedDict

from .ffmpeg import take_snapshot
from .vtt import extract_transcript_start_times, time_string_to_seconds

logger = logging.getLogger(__name__)


def similar_snapshots(snapshot1_path: str, snapshot2_path: str, percent: int):
    """Check if two snapshots are similar"""
    command = [
        "compare",
        "-metric",
        "DSSIM",
        snapshot1_path,
        snapshot2_path,
        "/dev/null",
    ]
    logger.info(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True)
    logger.debug(f"Result: {result}")

    normalized_mean_error = float(result.stderr)
    percentage_diff = (1 - normalized_mean_error) * 100

    return percentage_diff > percent


async def create_snapshots_at_time_increments(
    source_file: str, dir: str, min_interval: float
):
    """
    If the file is a video, create snapshots at the start time of each summary,
    respecting a minimum interval between snapshots.

    :param source_file: Path to the video file.
    :param dir: Directory to save snapshots.
    :param min_interval: Minimum interval between snapshots in seconds.
    """
    if os.path.exists(f"{dir}/snapshots/index.html"):
        logger.info("Snapshots already exists, skipping...")
        return

    start_times = extract_transcript_start_times(dir)
    logger.debug("Start times: %s", start_times)

    previous_snapshot_time = 0
    previous_snapshot_path = None

    for start_time in start_times:
        current_time = time_string_to_seconds(start_time)
        if (current_time - previous_snapshot_time) < min_interval:
            continue  # Skip if the interval is less than the minimum

        snapshot_filename = start_time.replace(":", "_") + ".jpg"
        snapshot_path = os.path.join(dir, "snapshots", snapshot_filename)
        if os.path.exists(snapshot_path):
            logger.info(f"Snapshot for {start_time} already exists, skipping...")
            continue

        os.makedirs(os.path.join(dir, "snapshots"), exist_ok=True)
        take_snapshot(source_file, start_time, snapshot_path)

        if previous_snapshot_path and similar_snapshots(
            previous_snapshot_path, snapshot_path, 90
        ):
            logger.debug(
                f"Snapshot for {start_time} is similar to previous snapshot, removing..."
            )
            os.remove(snapshot_path)
            continue

        previous_snapshot_time = current_time
        previous_snapshot_path = snapshot_path


class SnapshotDict(TypedDict):
    start: str
    source: str

def create_snapshots_file(dir: str) -> List[SnapshotDict]:
    os.makedirs(os.path.join(dir, "snapshots"), exist_ok=True)
    snapshots_file = os.path.join(dir, "snapshots", "snapshots.json")
    snapshot_files = [f for f in os.listdir(os.path.join(dir, "snapshots")) if f.endswith(".jpg")]

    # Generate HTML for each snapshot
    snapshots_json = [SnapshotDict(start=os.path.splitext(s)[0].replace("_", ":"), source=f"snapshots/{s}") for s in snapshot_files]
    logger.info("Saving snapshots to file...")
    with open(snapshots_file, "w") as file:
        file.write(json.dumps(snapshots_json, indent=2))

    return snapshots_json
