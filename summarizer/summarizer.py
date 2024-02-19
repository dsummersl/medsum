import asyncio
import logging
import os
import shutil
import json
import subprocess
import sys
from functools import wraps
from html.parser import HTMLParser

import click

from .ffmpeg import create_lower_quality_mp3, file_contains_video_or_audio
from .ffmpeg import logger as ffmpeg_logger
from .templates import run_time_chain, run_clif_chain, run_title_chain
from .snapshots import (
    create_snapshots_at_time_increments,
    create_snapshots_file,
    logger as snapshots_logger,
)
from .llm import create_transcript, generate_summary, convert_transcript_to_json


logger = logging.getLogger(__name__)

this_file = os.path.abspath(__file__)
this_dir = os.path.dirname(this_file)
with open(os.path.join(this_dir, "template.html"), "r") as file:
    HTML_TEMPLATE = (
        file.read()
        .replace("{", "{{")
        .replace("}", "}}")
        .replace("[[", "{")
        .replace("]]", "}")
    )


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


async def update_html(dir: str, output_path: str, title: str):
    """Generate an index.html and dir-name html file for the directory"""
    index_path = os.path.join(dir, "index.html")
    dir_path = os.path.join(dir, f"{output_path}.html")

    with open(os.path.join(dir, "chapters.json"), "r") as file:
        chapters = file.read()

    with open(os.path.join(dir, "title.json"), "r") as file:
        title_data = json.loads(file.read())

    with open(os.path.join(dir, "transcript.json"), "r") as file:
        transcript = file.read()

    snapshots = ""
    if os.path.exists(os.path.join(dir, "snapshots/snapshots.json")):
        with open(os.path.join(dir, "snapshots/snapshots.json"), "r") as file:
            snapshots = file.read()

    logger.info("Generating index.html...")

    logger.info(f"Index path: {index_path}")
    with open(index_path, "w") as file:
        file.write(
            HTML_TEMPLATE.format(
                title=title or title_data["title"],
                description=title_data["description"],
                chapters=chapters,
                transcript=transcript,
                snapshots=snapshots,
            )
        )

    logger.info(f"Dir HTML path: {dir_path}")
    with open(dir_path, "w") as file:
        file.write(
            HTML_TEMPLATE.format(
                title=output_path,
                description=title_data["description"],
                chapters=chapters,
                transcript=transcript,
                snapshots=snapshots,
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
    summary_path = os.path.join(dir, "summary.json")

    parser = SummaryHTMLParser()
    with open(summary_path, "r") as file:
        parser.feed(file.read())
    return parser.start_times


async def update_transcript(dirname: str, quiet: bool, transcript: str):
    print("Creating transcript...") if not quiet else None
    transcript_json = []
    if transcript:
        logger.info(f"Using supplied transcript: {transcript}")
        os.makedirs(dirname, exist_ok=True)
        if transcript != f"{dirname}/transcript.vtt":
            shutil.copy(transcript, f"{dirname}/transcript.vtt")
        transcript_json = convert_transcript_to_json(f"{dirname}/transcript.vtt")
    elif not os.path.exists(f"{dir}/transcript.json"):
        print("Generating transcript...") if not quiet else None
        transcript_json = await create_transcript(f"{dirname}/audio.mp3", dirname)
    return transcript_json


async def update_snapshots(dirname: str, file_path: str, has_video: bool, quiet: bool, snapshot_min_secs: int, transcript_json):
    if has_video:
        print("Generating snapshots...") if not quiet else None
        await create_snapshots_at_time_increments(file_path, dirname, snapshot_min_secs, transcript_json)
    create_snapshots_file(dirname)


def update_time_summary(dirname: str, quiet: bool, transcript_type: str, transcript_json):
    if transcript_type == "time":
        chain = run_time_chain
    elif transcript_type == "clif":
        chain = run_clif_chain
    else:
        print(f"Template {transcript_type} not found, exiting...") if not quiet else None
        return sys.exit(1)

    print("Generating summary...") if not quiet else None
    transcript_text = "\n".join(
        [f"id({i})|start({s['start']}) : {s['text']}" for i, s in enumerate(transcript_json)]
    )

    chapters_json = generate_summary(
        chain,
        transcript_text,
        os.path.join(dirname, "chapters.json"),
        quiet,
    )

    return chapters_json


def update_title(dirname: str, quiet: bool, chapters_json):
    print("Generating title...") if not quiet else None
    chapters = "Sections:\n" + "\n".join(
        [f"{s['title']} : {s['conclusion']}" for s in chapters_json]
    )
    generate_summary(
        run_title_chain, chapters, os.path.join(dirname, "title.json"), quiet
    )


async def update_all(
    file_path: str,
    dirname: str,
    template: str,
    title: str,
    transcript: str,
    snapshot_min_secs: int,
    has_video: bool,
    quiet: bool,
):
    transcript_json = await update_transcript(dirname, quiet, transcript)

    await update_snapshots(dirname, file_path, has_video, quiet, snapshot_min_secs, transcript_json)

    chapters_json = update_time_summary(dirname, quiet, template, transcript_json)

    update_title(dirname, quiet, chapters_json)

    last_dir = os.path.basename(os.path.dirname(dirname + "/fake.txt"))
    await update_html(dirname, last_dir, title)


@click.command()
@click.argument("file_path")
@click.option(
    "--transcript",
    type=click.Path(exists=True),
    help="Path to supplied transcript (default: auto-generated)",
)
@click.option("--output", "-o", default=None, help="Where to drop the output files")
@click.option(
    "--open/--no-open",
    "-o",
    default=False,
    help="Open the index.html file in a browser",
)
@click.option(
    "--snapshots/--no-snapshots", default=True, help="Create snapshots if possible"
)
@click.option(
    "--title", help="Specify a title for the summary (default: auto-generated)"
)
@click.option("--template", default="time", type=click.Choice(["time", "clif"]), help="Specify a built-in LLM template to generate summary (time, clif) (default: time)")
@click.option("--quiet", "-q", default=False, help="Suppress any console output")
@click.option(
    "--snapshot-min-secs",
    default=5,
    help="Minimum interval between video snapshots in seconds (default: 10)",
)
@click.option(
    "--level",
    "-l",
    default="WARNING",
    help="Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@coro
async def summarize(
    transcript,
    file_path,
    output,
    open,
    title,
    template,
    quiet,
    level,
    snapshot_min_secs,
    snapshots,
):
    """Summarize a video or audio file"""
    logging.basicConfig(level=level)
    logger.setLevel(level)
    ffmpeg_logger.setLevel(level)
    snapshots_logger.setLevel(level)

    logger.debug(f"Logging level: {level}")

    output = output if output else "."
    output_dirname = "_".join(os.path.basename(file_path).split(".")[0:-1]).replace(
        " ", "_"
    )
    dirname = f"{output}/{output_dirname}"

    logger.info(f"Output directory: {dirname}")

    has_video, has_audio = file_contains_video_or_audio(file_path)
    if not has_audio:
        print("File does not contain audio, exiting...") if not quiet else None
        return sys.exit(1)

    logger.debug(f"Has video: {has_video}")
    logger.debug(f"Has audio: {has_audio}")

    print("Generating audio sample...") if not quiet else None
    create_lower_quality_mp3(file_path, dirname)

    await update_all(
        file_path,
        dirname,
        template,
        title,
        transcript,
        snapshot_min_secs,
        has_video and snapshots,
        quiet,
    )

    if open:
        logger.info("Opening index.html in browser...")
        subprocess.Popen(["open", f"{dirname}/index.html"])


if __name__ == "__main__":
    summarize()
