import logging
from os.path import dirname
import time
import os
from typing import Dict, List
import yaml
import json
from webvtt import WebVTT

from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI


# https://github.com/langchain-ai/langchain/issues/10415 -- you can set this as a parameter

# Chunk size (number of characters times the estimated characters per token)
CHUNK_SIZE = 12000 * 2
# CHUNK_SIZE = 3000 * 2
llm = ChatOpenAI(
    model="gpt-3.5-turbo-16k"
    # temperature=0.0,
    # openai_api_base="http://localhost:8080/v1",
)

logger = logging.getLogger(__name__)
openai_client = AsyncOpenAI()


def seconds_to_hms(seconds: float) -> str:
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


def convert_transcript_to_json(transcript_path: str) -> List[Dict]:
    """
    Convert VTT transcript text to JSON format.
    """
    vtt = WebVTT.read(transcript_path)
    entries = [
        {
            "start": seconds_to_hms(caption.start_in_seconds),
            "end": seconds_to_hms(caption.end_in_seconds),
            "text": caption.text.strip(),
        }
        for caption in vtt
    ]
    with open(f"{dirname(transcript_path)}/transcript.json", "w") as f:
        f.write(json.dumps(entries, indent=2))
    return entries


async def create_transcript(media_path: str, dir: str) -> List[Dict]:
    """Use openai speech-to-text to extract audio, and save it to 'dir/transcript.json'"""
    if not os.path.exists(f"{dir}/transcript.json"):
        with open(media_path, "rb") as f:
            logger.info("Transcribing audio...")
            transcript = await openai_client.audio.transcriptions.create(
                file=f, model="whisper-1", response_format="vtt"
            )
            logger.info("Transcription complete!")

            #  Save the transcription to 'dir/transcript.md'
            logger.info("Saving transcript...")
            os.makedirs(dir, exist_ok=True)

            with open(f"{dir}/transcript.vtt", "w") as f:
                f.write(transcript)
            logger.info("Transcript saved!")
    else:
        logger.info("Transcript already exists, skipping...")
        return json.loads(open(f"{dir}/transcript.json").read())

    return convert_transcript_to_json(f"{dir}/transcript.vtt")


def generate_summary(
    chain,
    dest: str,
    quiet: bool,
) -> List[Dict]:
    """Summarize a text file, and save it to a destination"""
    if os.path.exists(dest):
        logger.info("Summary already exists, skipping...")
        return json.loads(open(dest).read())

    logger.info("Generating summary...")

    summaries = chain(llm)

    logger.info("Joining summaries, and saving...")
    logger.debug(summaries)

    with open(dest, "w") as file:
        file.write(json.dumps(summaries, indent=2))

    return summaries
