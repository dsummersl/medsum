import asyncio
from functools import wraps
import os

import click
from openai import AsyncOpenAI
from openai.types.audio import Transcription
from markdown2 import markdown


# Constants
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.m4a']

client = AsyncOpenAI()


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


async def create_transcript(media_path: str, dir: str):
    """ Use openai speech-to-text to extract audio, and save it to 'dir/transcript.md' """
    #  Call openai to transcribe the audio
    with open(media_path, 'rb') as f:
        print("Transcribing audio...")
        transcript = await client.audio.transcriptions.create(file=f, model='whisper-1', response_format='vtt')
        print("Transcription complete!")

    #  Save the transcription to 'dir/transcript.md'
    print("Saving transcript...")
    os.makedirs(dir, exist_ok=True)
    with open(f'{dir}/transcript.md', 'w') as f:
        f.write(transcript)
    print("Transcript saved!")


def transcribe_audio(audio_path):
    # Transcribe audio to text
    pass

def summarize_transcription(transcription):
    # Use OpenAI to summarize the transcription
    pass

def extract_snapshots(video_path, timestamps):
    # Extract snapshots from the video at given timestamps
    pass

def integrate_snapshots_in_summary(summary, snapshots):
    # Integrate snapshots in the markdown summary
    pass

# CLI Command
@click.command()
@click.argument('file_path')
@click.option('--dir_name', default=None, help='Custom directory name')
@coro
async def main(file_path, dir_name):
    dirname = dir_name if dir_name else os.path.basename(file_path).split('.')[0]
    await create_transcript(file_path, dirname)

if __name__ == '__main__':
    main()
