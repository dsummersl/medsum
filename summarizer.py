import logging
import asyncio
import subprocess
from functools import wraps
import os

import click
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Constants
VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".m4a"]

client = AsyncOpenAI()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Audio Transcript Summary</title>
    <style>
        body {{
            margin: 20px;
            font-family: Arial, sans-serif;
        }}

        .container {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }}

        .summary-container {{
            border-right: 1px solid #ddd;
        }}

        .vtt-container {{
            white-space: pre-wrap; /* To preserve formatting of VTT file */
            display: none;
        }}

        .audio-container {{
            position: fixed;
            bottom: 20px; /* Padding from the bottom */
            left: 50%;
            transform: translateX(-50%);
        }}

        div[data-summary-number] {{
            cursor: pointer;
            margin-bottom: 10px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            transition: background-color 0.3s ease;
        }}

          div[data-summary-number]:hover,
        div[data-summary-number].highlight {{
            background-color: #f0f0f0;
        }}

        div[data-summary-number].playing {{
            background-color: #ffdab9; /* light orange */
        }}
    </style>
    <script>
        function playSegment(start, summaryNumber) {{
            var audioPlayer = document.getElementById('audioPlayer');
            var source = document.getElementById('audioSource');

            source.src = './audio.mp3#t=' + start;
            audioPlayer.load();
            audioPlayer.play();

            highlightSummary(summaryNumber)
        }}

        function highlightSummary(summaryNumber) {{
            var summaries = document.querySelectorAll('.summary-container div[data-summary-number]');
            summaries.forEach(function(div) {{
                if (div.getAttribute('data-summary-number') === summaryNumber) {{
                    div.classList.add('playing');
                }} else {{
                    div.classList.remove('playing');
                }}
            }});
        }}


        function updateHighlightBasedOnTime() {{
            var audioPlayer = document.getElementById('audioPlayer');
            var currentTime = audioPlayer.currentTime; // Current playback time in seconds

            var summaries = document.querySelectorAll('.summary-container div[data-summary-number]');
            summaries.forEach(function(div) {{
                var startTime = timeStringToSeconds(div.getAttribute('data-start'));
                var endTime = timeStringToSeconds(div.getAttribute('data-end'));

                if (currentTime >= startTime && currentTime <= endTime) {{
                    div.classList.add('playing');
                }} else {{
                    div.classList.remove('playing');
                }}
            }});
        }}

        function timeStringToSeconds(timeString) {{
            var hm = timeString.split(':'); // split it at the colons
            return (+hm[0]) * 60 + (+hm[1]);
        }}

        function setupEventListeners() {{
            var summaryDivs = document.querySelectorAll('div[data-summary-number]');
            summaryDivs.forEach(function(div) {{
                div.addEventListener('click', function() {{
                  var start = this.getAttribute('data-start');
                  var summaryNumber = this.getAttribute('data-summary-number');
                  playSegment(start, summaryNumber);
                }});
            }});

            var audioPlayer = document.getElementById('audioPlayer');
            audioPlayer.addEventListener('timeupdate', updateHighlightBasedOnTime);
        }}

        window.onload = setupEventListeners;
    </script>
</head>
<body>
    <div class="audio-container">
        <audio id="audioPlayer" controls>
            <source id="audioSource" src="./audio.mp3" type="audio/mpeg" />
            Your browser does not support the audio element.
        </audio>
    </div>

    <div class="container summary-container">
    {summary}
    </div>

    <div class="container vtt-container">
    {transcript}
    </div>

</body>
</html>
"""

SUMMARY_TEMPLATE = """\
Transcript:
{transcript_text}
***
Create a list that summarizes topics discussed and parties involved in the transcript above.
Capture topics briefly (only highlight key points or issues).
Key points are things that were mentioned frequently in the discussion, or decisions that were made.
Include any names of people, places, or times (who, what, when) that are mentioned in the transcript, or you can be inferred by the context.
Give a response in html. Highlight key points with <mark> tags.
Use this output format:

<div data-summary-number="1" data-start="00:00" data-end="00:10">
  <b>00:00 - 00:10</b>
  <ul>
    <li>Discussed the weather, what was happening over the weekend.</li>
  </ul>
</div>
<div data-summary-number="2" data-start="03:15" data-end="05:05">
  <b>03:15 - 05:05</b>
  <ul>
    <li>
      Started the agenda: <b>vacation planning</b>, <b>action items</b>.
    </li>
  </ul>
</div>
<div data-summary-number="3" data-start="05:05" data-end="08:13">
  <b>05:05 - 08:13</b>
  <ul>
    <li>Started talking about <b>vacation planning</b>.</li>
    <li>
      Jerry discussed what kind of socks, pants and shoes should be brought.
    </li>
    <li>Sheryll brought up the idea of bringing a tent.</li>
    <li><mark>Decided to bring a tent, and personal items</mark>.</li>
  </ul>
</div>
<div data-summary-number="4" data-start="08:13" data-end="10:15">
  <b>08:13 - 10:15</b>
  <ul>
    <li>Started talking about <b>action items</b></li>
    <li>
      People expressed a need to
      <mark>have another meeting after vacation</mark>.
    </li>
  </ul>
</div>
***
"""


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
        "-i",
        source_file,
        "-codec:a",
        "libmp3lame",
        "-qscale:a",
        "9",
        output_file,
    ]
    logger.info(f"Running command: {' '.join(command)}")
    subprocess.run(command)


async def create_index(dir: str, force: bool):
    """Generate an index.html file for the directory"""
    index_path = os.path.join(dir, "index.html")

    if not force and os.path.exists(index_path):
        logger.info("Index already exists, skipping...")
        return

    with open(os.path.join(dir, "summary.html"), "r") as file:
        summary = file.read()

    with open(os.path.join(dir, "transcript.vtt"), "r") as file:
        transcript = file.read()

    logger.info("Generating index.html...")

    with open(index_path, "w") as file:
        file.write(HTML_TEMPLATE.format(summary=summary, transcript=transcript))


@click.command()
@click.argument("file_path")
@click.option("--output-dir", default=None, help="Output directory")
@click.option("--force", default=False, help="Overwrite any existing files")
@click.option("--level", default=logging.DEBUG, help="Log level")
@coro
async def main(file_path, output_dir, force, level):
    logging.basicConfig(level=level)

    dirname = (
        output_dir
        if output_dir
        else "_".join(os.path.basename(file_path).split(".")[0:-1]).replace(" ", "_")
    )
    logger.info(f"Output directory: {dirname}")
    create_lower_quality_mp3(file_path, dirname, force)
    await create_transcript(f"{dirname}/audio.mp3", dirname, force)
    await generate_summary(dirname, force)
    await create_index(dirname, force)


if __name__ == "__main__":
    main()
