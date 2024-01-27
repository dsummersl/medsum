import logging
import os

from langchain_community.llms import OpenAI
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion


os.environ["OPENAI_API_BASE"] = "http://localhost:8081/v1"
os.environ["OPENAI_API_HOST"] = "http://localhost:8081"
llm = OpenAI()

logger = logging.getLogger(__name__)
openai_client = AsyncOpenAI()


async def create_transcript(media_path: str, dir: str, force: bool):
    """Use openai speech-to-text to extract audio, and save it to 'dir/transcript.vtt'"""
    if not force and os.path.exists(f"{dir}/transcript.vtt"):
        logger.info("Transcript already exists, skipping...")
        return

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


async def chat(prompt: str) -> ChatCompletion:
    """Chat with the LLM"""
    logger.info("Chatting with LLM...")
    return await openai_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}], model="gpt-3.5-turbo-16k"
    )
