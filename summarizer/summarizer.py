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
from .templates import SUMMARY_TEMPLATE, CHAPTERS_TEMPLATE, TITLE_TEMPLATE
from .snapshots import create_snapshots_at_time_increments, create_snapshots_file, logger as snapshots_logger
from .llm import create_transcript, generate_summary

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


async def create_index(dir: str, output_path: str, title: str):
    """Generate an index.html and dir-name html file for the directory"""
    index_path = os.path.join(dir, "index.html")
    dir_path = os.path.join(dir, f"{output_path}.html")

    with open(os.path.join(dir, "summary.json"), "r") as file:
        summary = file.read()

    with open(os.path.join(dir, "chapters.json"), "r") as file:
        chapters = file.read()

    with open(os.path.join(dir, "title.json"), "r") as file:
        title_data = json.loads(file.read())

    with open(os.path.join(dir, "transcript.vtt"), "r") as file:
        transcript = file.read()

    snapshots = ""
    if os.path.exists(os.path.join(dir, "snapshots/index.html")):
        with open(os.path.join(dir, "snapshots/index.html"), "r") as file:
            snapshots = file.read()

    logger.info("Generating index.html...")

    logger.info(f"Index path: {index_path}")
    with open(index_path, "w") as file:
        file.write(
            HTML_TEMPLATE.format(
                title=title or title_data['title'],
                description=title_data['description'],
                summary=summary,
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
                description=title_data['description'],
                summary=summary,
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


async def update_index(
    file_path: str,
    dirname: str,
    title: str,
    transcript:str,
    summary_min_mins: int,
    snapshot_min_secs:int,
    has_video: bool,
    quiet:bool,
):
    print("Creating transcript...") if not quiet else None
    if transcript:
        logger.info(f"Using supplied transcript: {transcript}")
        os.makedirs(dirname, exist_ok=True)
        if transcript != f"{dirname}/transcript.vtt":
            shutil.copy(transcript, f"{dirname}/transcript.vtt")
    elif not os.path.exists(f"{dir}/transcript.vtt"):
        print("Generating transcript...") if not quiet else None
        await create_transcript(f"{dirname}/audio.mp3", dirname)

    print("Generating summary...") if not quiet else None
    transcript_path = os.path.join(dirname, "transcript.vtt")
    summary_path = os.path.join(dirname, "summary.json")
    await generate_summary(transcript_path, summary_path, SUMMARY_TEMPLATE, quiet, summary_min_mins)

    print("Generating chapters...") if not quiet else None
    summary_to_chapters_path = os.path.join(dirname, "chapters.txt")
    source_sections = json.loads(open(summary_path).read())
    sources = "\n".join([f"{s['start']} {s['title']} : {s['description']}" for s in source_sections])
    with open(summary_to_chapters_path, "w") as f:
        f.write(sources)

    chapters_path = os.path.join(dirname, "chapters.json")
    await generate_summary(summary_to_chapters_path, chapters_path, CHAPTERS_TEMPLATE, quiet, None)

    print("Generating title...") if not quiet else None
    summary_to_chapters_path = os.path.join(dirname, "titles.txt")
    chapter_parts = json.loads(open(chapters_path).read())
    chapters = "\n".join([f"{s['start']} {s['title']} : {s['description']}" for s in chapter_parts])
    with open(summary_to_chapters_path, "w") as f:
        f.write(chapters)
    title_path = os.path.join(dirname, "title.json")
    await generate_summary(summary_to_chapters_path, title_path, TITLE_TEMPLATE, quiet, None)

    if has_video:
        print("Generating snapshots...") if not quiet else None
        await create_snapshots_at_time_increments(
            file_path, dirname, snapshot_min_secs
        )
    create_snapshots_file(dirname)

    last_dir = os.path.basename(os.path.dirname(dirname + "/fake.txt"))
    await create_index(dirname, last_dir, title)


@click.group()
def cli():
    pass


@click.command("update-index")
@click.argument("summary_path")
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
    "--title", help="Specify a title for the summary (default: auto-generated)"
)
@coro
async def update_index_cli(summary_path, snapshot_min_secs, summary_min_mins, quiet, title):
    """Regenerate the transcript, summary, and index of a previously summarized directory.

    This command is useful if you want to refresh/update an existing summary:
    - Regenerates the summary if it doesn't exist.
    - Regenerates the transcript if it doesn't exist.
    - Regenerates the HTML files (you can get the latest version created by this script).

    Limitations:
    - Since it doesn't have access to the original media file, it can't generate
      snapshots (but you can trim out any snapshots from the directory, and
      they'll be removed from the final HTML file).
    """
    await update_index(
        None,
        summary_path,
        summary_path + "/transcript.vtt"
        if os.path.exists(summary_path + "/transcript.vtt")
        else None,
        title,
        summary_min_mins,
        snapshot_min_secs,
        False,
        quiet
    )


@click.command()
@click.argument("file_path")
@click.option(
    "--transcript",
    "-t",
    type=click.Path(exists=True),
    help="Path to supplied transcript (if supplied, medsum won't generate one)",
)
@click.option("--output", "-o", default=None, help="Where to drop the output files")
@click.option("--open/--no-open", "-p", default=False, help="Open the index.html file in a browser")
@click.option(
    "--snapshots/--no-snapshots", default=True, help="Create snapshots if possible"
)
@click.option(
    "--title", help="Specify a title for the summary (default: auto-generated)"
)
@click.option("--quiet", "-q", default=False, help="Suppress printing activities")
@click.option(
    "--snapshot-min-secs",
    default=5,
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
    transcript,
    file_path,
    output,
    open,
    title,
    quiet,
    level,
    summary_min_mins,
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

    await update_index(
        file_path,
        dirname,
        title,
        transcript,
        summary_min_mins,
        snapshot_min_secs,
        has_video and snapshots,
        quiet,
    )

    if open:
        logger.info("Opening index.html in browser...")
        subprocess.Popen(["open", f"{dirname}/index.html"])


cli.add_command(summarize)
cli.add_command(update_index_cli)


if __name__ == "__main__":
    cli()
