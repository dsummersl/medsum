import textwrap
import asyncio
import subprocess
from functools import wraps
import os

import click
from openai import AsyncOpenAI


# Constants
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.m4a']

client = AsyncOpenAI()


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


async def create_transcript(media_path: str, dir: str):
    """ Use openai speech-to-text to extract audio, and save it to 'dir/transcript.vtt' """
    # TODO support detecting files over 25mb and splitting them up
    #  Call openai to transcribe the audio
    with open(media_path, 'rb') as f:
        print("Transcribing audio...")
        transcript = await client.audio.transcriptions.create(file=f, model='whisper-1', response_format='vtt')
        print("Transcription complete!")

    #  Save the transcription to 'dir/transcript.md'
    print("Saving transcript...")
    os.makedirs(dir, exist_ok=True)
    with open(f'{dir}/transcript.vtt', 'w') as f:
        f.write(transcript)
    print("Transcript saved!")


async def generate_summary(dir: str):
    """ Use openai to summarize the VTT formatted transcript, and save it to 'dir/summary.html' """
    transcript_path = os.path.join(dir, "transcript.vtt")
    summary_path = os.path.join(dir, "summary.html")

    with open(transcript_path, 'r') as file:
        transcript_text = file.read()

    response = await client.chat.completions.create(
        messages=[{
                "role": "user",
                "content": textwrap.dedent(f"""\
                    Transcript:
                    {transcript_text}
                    ***
                    Create a list of that summarizes topics discussed parties in the transcript above.
                    Each section should start with a markdown URL of referencing the relevant time in the audio clip.
                    Include names of people who that you think were talking, or were mentioned.
                    Give a response in html. Highlight key points with <mark> tags.
                    Use this output format:

                    <html>

                    <body>
                      <h1>Summary</h1>
                      <p>
                        <b>00:00 - 00:10</b>
                        <audio controls>
                          <source src="./audio.mp3#t=00:00:00" type="audio/mpeg" />
                        </audio>
                      <ul>
                        <li>Discussed the weather, what was happening over the weekend.
                        </li>
                      </ul>
                      </p>
                      <p>
                        <b>03:15 - 05:05</b>
                        <audio controls>
                          <source src="./audio.mp3#t=00:03:15" type="audio/mpeg" />
                        </audio>
                      <ul>
                        <li>Started the agenda: <b>vacation planning</b>, <b>action items</b>.
                        </li>
                      </ul>
                      </p>
                      <p>
                        <b>05:05 - 8:13</b>
                        <audio controls>
                          <source src="./audio.mp3#t=00:05:05" type="audio/mpeg" />
                        </audio>
                      <ul>
                        <li>Started talking about <b>vacation planning</b>.
                        </li>
                        <li>Jerry discussed what kind of socks, pants and shoes should be brought.
                        </li>
                        <li>Sheryll brought up the idea of bringing a tent.
                        </li>
                      </ul>
                      </p>
                      <p>
                        <b>08:13 - 10:15</b>
                        <audio controls>
                          <source src="./audio.mp3#t=00:08:13" type="audio/mpeg" />
                        </audio>
                      <ul>
                        <li>Started talking about <b>action items</b>
                        </li>
                        <li>People expressed a need to have another meeting after vacation.
                        </li>
                      </ul>
                      </p>
                    </body>


                    </html>
                    ***
                    """)
            }],
        # model="gpt-3.5-turbo"
        model="gpt-4"
    )
    summary = response.choices[0].message.content.strip()

    # Save the summary to a markdown file
    with open(summary_path, 'w') as file:
        file.write(summary)


def create_lower_quality_mp3(source_file: str, dir: str):
    """
    Generates a lower quality MP3 file from the source file using FFmpeg.

    :param source_file: Path to the source audio file.
    :param output_dir: Directory where the lower quality MP3 file will be saved.
    """
    output_file = os.path.join(dir, "audio.mp3")

    command = [
        "ffmpeg",
        "-i", source_file,
        "-codec:a", "libmp3lame",
        "-qscale:a", "5",
        output_file
    ]
    subprocess.run(command)


@click.command()
@click.argument('file_path')
@click.option('--dir_name', default=None, help='Custom directory name')
@coro
async def main(file_path, dir_name):
    dirname = dir_name if dir_name else os.path.basename(file_path).split('.')[0]
    await create_transcript(file_path, dirname)
    await generate_summary(dirname)
    create_lower_quality_mp3(file_path, dirname)

if __name__ == '__main__':
    main()
