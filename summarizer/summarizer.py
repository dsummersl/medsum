import asyncio
import logging
import os
import re
import shutil
import subprocess
import sys
from functools import wraps
from html.parser import HTMLParser

import click
from openai import AsyncOpenAI

from .ffmpeg import create_lower_quality_mp3, file_contains_video_or_audio
from .ffmpeg import logger as ffmpeg_logger
from .ffmpeg import take_snapshot, time_string_to_seconds
from .templates import SUMMARY_TEMPLATE

logger = logging.getLogger(__name__)
client = AsyncOpenAI()

this_file = os.path.abspath(__file__)
this_dir = os.path.dirname(this_file)
with open(os.path.join(this_dir, "template.html"), "r") as file:
    HTML_TEMPLATE = file.read().replace("{", "{{").replace("}", "}}").replace("[[", "{").replace("]]", "}")


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


async def create_transcript(media_path: str, dir: str, force: bool):
    """Use openai speech-to-text to extract audio, and save it to 'dir/transcript.vtt'"""
    if not force and os.path.exists(f"{dir}/transcript.vtt"):
        logger.info("Transcript already exists, skipping...")
        return

    with open(media_path, "rb") as f:
        logger.info("Transcribing audio...")
        transcript = await client.audio.transcriptions.create(
            file=f, model="whisper-1", response_format="vtt"
        )
        logger.info("Transcription complete!")

    #  Save the transcription to 'dir/transcript.md'
    logger.info("Saving transcript...")
    os.makedirs(dir, exist_ok=True)

    with open(f"{dir}/transcript.vtt", "w") as f:
        f.write(transcript)
    logger.info("Transcript saved!")


async def generate_summary(dir: str, force: bool, quiet: bool, minimum_summary_minutes: int):
    """Use openai to summarize the VTT formatted transcript, and save it to 'dir/summary.html'"""
    transcript_path = os.path.join(dir, "transcript.vtt")
    summary_path = os.path.join(dir, "summary.html")

    if not force and os.path.exists(summary_path):
        logger.info("Summary already exists, skipping...")
        return

    with open(transcript_path, "r") as file:
        transcript_text = file.read()

    logger.info("Generating summary...")

    # Chunk size (number of characters times the estimated characters per token)
    chunk_size = 12000 * 2

    # Split the transcript text into chunks
    chunks = [
        transcript_text[i : i + chunk_size]
        for i in range(0, len(transcript_text), chunk_size)
    ]

    # List to hold summaries of each chunk
    summaries = []

    count = 1
    for chunk in chunks:
        print(f"Generating summary for chunk {count} of {len(chunks)}...") if not quiet else None
        prompt = SUMMARY_TEMPLATE.format(transcript_text=chunk, minimum_summary_minutes=minimum_summary_minutes)
        response = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}], model="gpt-3.5-turbo-16k"
        )
        # Append the summary of the chunk to the summaries list
        summaries.append(response.choices[0].message.content.strip())
        count += 1

    logger.info("Joining summaries, and saving...")
    # Combine all summaries into one
    combined_summary = "\n".join(summaries)

    # Save the combined summary to a markdown file
    with open(summary_path, "w") as file:
        file.write(combined_summary)


async def create_index(dir: str, output_path: str, force: bool):
    """Generate an index.html and dir-name html file for the directory"""
    index_path = os.path.join(dir, "index.html")
    dir_path = os.path.join(dir, f"{output_path}.html")

    with open(os.path.join(dir, "summary.html"), "r") as file:
        summary = file.read()

    with open(os.path.join(dir, "transcript.vtt"), "r") as file:
        transcript = file.read()

    snapshots = ""
    if os.path.exists(os.path.join(dir, "snapshots.html")):
        with open(os.path.join(dir, "snapshots.html"), "r") as file:
            snapshots = file.read()

    logger.info("Generating index.html...")

    logger.info(f"Index path: {index_path}")
    if force or not os.path.exists(index_path):
        with open(index_path, "w") as file:
            file.write(
                HTML_TEMPLATE.format(
                    title=output_path,
                    summary=summary,
                    transcript=transcript,
                    snapshots=snapshots,
                )
            )
    else:
        logger.info("Index already exists, skipping...")

    logger.info(f"Dir HTML path: {dir_path}")
    if force or not os.path.exists(dir_path):
        with open(dir_path, "w") as file:
            file.write(
                HTML_TEMPLATE.format(
                    title=output_path, summary=summary, transcript=transcript,
                    snapshots=snapshots
                )
            )
    else:
        logger.info("Dir HTML already exists, skipping...")


def similar_snapshots(snapshot1_path: str, snapshot2_path: str, percent: int):
    """Check if two snapshots are similar"""
    command = [
        "compare",
        "-metric",
        "MAE",
        snapshot1_path,
        snapshot2_path,
        "/dev/null",
    ]
    logger.info(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True)
    logger.debug(f"Result: {result}")

    match = re.search(r"\((\d+(\.\d+)?)\)", result.stderr.decode("utf-8"))
    if not match:
        return False

    normalized_mean_error = float(match.group(1))
    percentage_diff = (1 - normalized_mean_error) * 100

    return percentage_diff > percent


async def create_snapshots_at_time_increments(
    source_file: str, dir: str, force: bool, min_interval: float
):
    """
    If the file is a video, create snapshots at the start time of each summary,
    respecting a minimum interval between snapshots.

    :param source_file: Path to the video file.
    :param dir: Directory to save snapshots.
    :param force: Force creation of snapshots even if they exist.
    :param min_interval: Minimum interval between snapshots in seconds.
    """
    if not force and os.path.exists(f"{dir}/snapshots.html"):
        logger.info("Snapshots already exists, skipping...")
        return

    start_times = extract_transcript_start_times(dir)
    logger.debug("Start times: %s", start_times)

    previous_snapshot_time = 0
    previous_snapshot_path = None
    snapshot_times = []

    for start_time in start_times:
        current_time = time_string_to_seconds(start_time)
        if (current_time - previous_snapshot_time) < min_interval:
            continue  # Skip if the interval is less than the minimum

        snapshot_filename = start_time.replace(":", "_") + ".jpg"
        snapshot_path = os.path.join(dir, snapshot_filename)
        if not force and os.path.exists(snapshot_path):
            logger.info(f"Snapshot for {start_time} already exists, skipping...")
            continue

        take_snapshot(source_file, start_time, snapshot_path)

        if previous_snapshot_path and similar_snapshots(
            previous_snapshot_path, snapshot_path, 90
        ):
            logger.debug(
                f"Snapshot for {start_time} is similar to previous snapshot, removing..."
            )
            os.remove(snapshot_path)
            # Update the previous snapshot time to the current time (since its similar to the current snapshot)
            previous_snapshot_time = current_time
            continue

        snapshot_times.append(start_time)
        previous_snapshot_time = current_time
        previous_snapshot_path = snapshot_path

    logger.info("Saving snapshots to file...")
    with open(os.path.join(dir, "snapshots.html"), "w") as file:
        file.write(
            "\n".join(
                [
                    f"<img data-start='{start}' src='{start.replace(':', '_') + '.jpg'}'>"
                    for start in snapshot_times
                ]
            )
        )


class SummaryHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.start_times = []

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            attrs_dict = dict(attrs)
            if "data-start" in attrs_dict:
                self.start_times.append(attrs_dict["data-start"])


def extract_summary_start_times(dir: str):
    summary_path = os.path.join(dir, "summary.html")

    parser = SummaryHTMLParser()
    with open(summary_path, "r") as file:
        parser.feed(file.read())
    return parser.start_times


def extract_transcript_start_times(dir: str):
    """
    Extracts start times from a VTT file.

    :param vtt_path: Path to the VTT file.
    :return: List of start times in seconds.
    """
    vtt_path = os.path.join(dir, "transcript.vtt")

    start_times = []
    time_pattern = re.compile(
        r"^(\d{2}:\d{2}:\d{2}).\d{3} --> \d{2}:\d{2}:\d{2}.\d{3}$"
    )
    with open(vtt_path, "r") as file:
        for line in file:
            match = time_pattern.search(line)
            if match:
                start_times.append(match.group(1))
    return start_times


async def update_index(summary_path, force, quiet):
    print("Creating HTML files...") if not quiet else None
    last_dir = os.path.basename(os.path.dirname(summary_path))
    await create_index(summary_path, last_dir, force)


@click.group()
def cli():
    pass


@click.command("update-index")
@click.argument("summary_path")
@click.option("--quiet", "-q", default=False, help="Suppress printing activities")
@coro
async def update_index_cli(summary_path, quiet):
    """ Regenerate the index.html and dir-name.html files in the directory """
    await update_index(summary_path, True, quiet)


@click.command()
@click.argument("file_path")
@click.option(
    "--transcript",
    "-t",
    type=click.Path(exists=True),
    help="Path to supplied transcript (if supplied, medsum won't generate one)",
)
@click.option("--output", "-o", default=None, help="Where to drop the output files")
@click.option(
    "--force/--no-force", "-f", default=False, help="Overwrite any existing files"
)
@click.option("--quiet", "-q", default=False, help="Suppress printing activities")
@click.option(
    "--snapshot-min-secs",
    default=10,
    help="Minimum interval between video snapshots in seconds (default: 10)",
)
@click.option(
    "--summary-min-mins",
    default=2,
    help="When summarizing, minimum number of minutes in each summary (default: 2)",
)
@click.option(
    "--level",
    "-l",
    default="WARNING",
    help="Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@coro
async def summarize(
    transcript, file_path, output, force, quiet, level, summary_min_mins, snapshot_min_secs
):
    """ Summarize a video or audio file """
    logging.basicConfig(level=level)
    logger.setLevel(level)
    ffmpeg_logger.setLevel(level)

    logger.debug(f"Logging level: {level}")
    logger.debug(f"Force: {force}")

    output = output if output else "."
    output_dirname = "_".join(os.path.basename(file_path).split(".")[0:-1]).replace(
        " ", "_"
    )
    dirname = f"{output}/{output_dirname}"

    logger.info(f"Output directory: {dirname}")

    has_video, has_audio = file_contains_video_or_audio(file_path)
    if not has_audio:
        logger.error("File does not contain audio, exiting...")
        return sys.exit(1)

    print("Generating audio sample...") if not quiet else None
    create_lower_quality_mp3(file_path, dirname, force)

    if transcript:
        logger.info(f"Using supplied transcript: {transcript}")
        os.makedirs(dirname, exist_ok=True)
        shutil.copy(transcript, f"{dirname}/transcript.vtt")
    if force or not os.path.exists(f"{dir}/transcript.vtt"):
        print("Generating transcript...") if not quiet else None
        await create_transcript(f"{dirname}/audio.mp3", dirname, force)

    print("Generating summary...") if not quiet else None
    await generate_summary(dirname, force, quiet, summary_min_mins)

    if has_video:
        print("Generating snapshots...") if not quiet else None
        await create_snapshots_at_time_increments(
            file_path, dirname, force, snapshot_min_secs
        )

    await update_index(output_dirname, force, quiet)


cli.add_command(summarize)
cli.add_command(update_index_cli)


if __name__ == "__main__":
    cli()
