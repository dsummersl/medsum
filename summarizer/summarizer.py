import asyncio
import logging
import os
import sys
from functools import wraps
from html.parser import HTMLParser

import click
from openai import AsyncOpenAI

from .ffmpeg import create_lower_quality_mp3, file_contains_video_or_audio
from .ffmpeg import logger as ffmpeg_logger
from .ffmpeg import take_snapshot
from .templates import HTML_TEMPLATE, SUMMARY_TEMPLATE

logger = logging.getLogger(__name__)
client = AsyncOpenAI()


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


async def generate_summary(dir: str, force: bool):
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
    chunk_size = 16000 * 2

    # Split the transcript text into chunks
    chunks = [
        transcript_text[i : i + chunk_size]
        for i in range(0, len(transcript_text), chunk_size)
    ]

    # List to hold summaries of each chunk
    summaries = []

    count = 1
    for chunk in chunks:
        logger.info(f"Generating summary for chunk {count} of {len(chunks)}...")
        # Create a prompt for each chunk
        prompt = SUMMARY_TEMPLATE.format(transcript_text=chunk)
        response = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}], model="gpt-3.5-turbo-16k"
        )
        # Append the summary of the chunk to the summaries list
        summaries.append(response.choices[0].message.content.strip())

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

    logger.info("Generating index.html...")

    logger.info(f"Index path: {index_path}")
    if force or not os.path.exists(index_path):
        with open(index_path, "w") as file:
            file.write(
                HTML_TEMPLATE.format(title=output_path, summary=summary, transcript=transcript)
            )
    else:
        logger.info("Index already exists, skipping...")

    logger.info(f"Dir HTML path: {dir_path}")
    if force or not os.path.exists(dir_path):
        with open(dir_path, "w") as file:
            file.write(HTML_TEMPLATE.format(title=output_path, summary=summary, transcript=transcript))
    else:
        logger.info("Dir HTML already exists, skipping...")


async def create_snapshots_at_time_increments(source_file: str, dir: str, force: bool):
    """If the file is a video, create snapshots at the start time of each summary"""
    # Path to the summary file
    summary_path = os.path.join(dir, "summary.html")

    # Read the summary file and extract start times
    start_times = extract_start_times(summary_path)
    logger.debug("Start times: %s", start_times)

    # Create snapshots
    for start_time in start_times:
        snapshot_filename = time_to_filename(start_time)
        snapshot_path = os.path.join(dir, snapshot_filename)
        if not force and os.path.exists(snapshot_path):
            logger.info(f"Snapshot for {start_time} already exists, skipping...")
            continue
        take_snapshot(source_file, start_time, snapshot_path)


class SummaryHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.start_times = []

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            attrs_dict = dict(attrs)
            if "data-start" in attrs_dict:
                self.start_times.append(attrs_dict["data-start"])


def extract_start_times(summary_path):
    parser = SummaryHTMLParser()
    with open(summary_path, "r") as file:
        parser.feed(file.read())
    return parser.start_times


def time_to_filename(time_string):
    # Convert time string to filename
    parts = time_string.split(":")
    return f"{parts[0]}_{parts[1]}.jpg"


@click.command()
@click.argument("file_path")
@click.option("--output-path", "-o", default=None, help="Where to drop the output files")
@click.option("--force", "-f", default=False, help="Overwrite any existing files")
@click.option(
    "--level", "-l",
    default="WARNING",
    help="Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@coro
async def main(file_path, output_path, force, level):
    logging.basicConfig(level=level)
    logger.setLevel(level)
    ffmpeg_logger.setLevel(level)

    logger.debug(f"Logging level: {level}")
    logger.debug(f"Force: {force}")

    output_path = output_path if output_path else "."
    output_dirname = "_".join(os.path.basename(file_path).split(".")[0:-1]).replace(
        " ", "_"
    )
    dirname = f"{output_path}/{output_dirname}"

    logger.info(f"Output directory: {dirname}")

    has_video, has_audio = file_contains_video_or_audio(file_path)
    if not has_audio:
        logger.error("File does not contain audio, exiting...")
        sys.exit(1)
        return

    create_lower_quality_mp3(file_path, dirname, force)
    await create_transcript(f"{dirname}/audio.mp3", dirname, force)
    await generate_summary(dirname, force)

    if has_video:
        await create_snapshots_at_time_increments(file_path, dirname, force)

    await create_index(dirname, output_dirname, force)


if __name__ == "__main__":
    main()
