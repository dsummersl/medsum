import logging
import os
import subprocess
import json

from .vtt import time_string_to_seconds

logger = logging.getLogger(__name__)


def file_contains_video_or_audio(file_path):
    """
    Uses ffprobe to determine if the file contains video or audio.

    :param file_path: Path to the media file.
    :return: A tuple (contains_video, contains_audio)
    """
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "stream=codec_type",
        "-of", "json",
        file_path
    ]

    logger.debug(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout

    try:
        ffprobe_output = json.loads(output)
        streams = ffprobe_output.get("streams", [])

        contains_video = any(stream["codec_type"] == "video" for stream in streams)
        contains_audio = any(stream["codec_type"] == "audio" for stream in streams)

        return contains_video, contains_audio
    except json.JSONDecodeError:
        raise ValueError("Could not parse ffprobe output")


def create_lower_quality_mp3(source_file: str, dir: str, force: bool):
    """
    Generates a lower quality MP3 file from the source file using FFmpeg.

    :param source_file: Path to the source audio file.
    :param output_dir: Directory where the lower quality MP3 file will be saved.
    """
    output_file = os.path.join(dir, "audio.mp3")

    if not force and os.path.exists(output_file):
        logger.info("Lower quality MP3 already exists, skipping...")
        return

    logger.info("Generating lower quality MP3...")

    os.makedirs(dir, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        source_file,
        "-codec:a",
        "libmp3lame",
        "-qscale:a",
        "9",
        output_file,
    ]
    logger.debug(f"Running command: {' '.join(command)}")
    suppress_output = not logger.isEnabledFor(logging.DEBUG)
    subprocess.run(
        command,
        stdout=subprocess.DEVNULL if suppress_output else None,
        stderr=subprocess.DEVNULL if suppress_output else None,
        check=True
    )


def take_snapshot(video_path, start_time, snapshot_path):
    # Use FFmpeg to take a snapshot at the start time
    command = [
        "ffmpeg",
        "-y",
        "-ss", str(time_string_to_seconds(start_time)),
        "-i", video_path,
        "-q:v", "5",
        "-frames:v", "1",
        snapshot_path
    ]
    logger.debug(f"Running command: {' '.join(command)}")
    suppress_output = not logger.isEnabledFor(logging.DEBUG)
    subprocess.run(
        command,
        stdout=subprocess.DEVNULL if suppress_output else None,
        stderr=subprocess.DEVNULL if suppress_output else None,
        check=True
    )
