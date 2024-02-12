import logging
import os
import yaml
import json

from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI


# https://github.com/langchain-ai/langchain/issues/10415 -- you can set this as a parameter
llm = ChatOpenAI(
    # temperature=0.0,
    # openai_api_base="http://localhost:8080/v1",
)

logger = logging.getLogger(__name__)
openai_client = AsyncOpenAI()


async def create_transcript(media_path: str, dir: str):
    """Use openai speech-to-text to extract audio, and save it to 'dir/transcript.vtt'"""
    if os.path.exists(f"{dir}/transcript.vtt"):
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


async def chat(prompt: str) -> str:
    """Chat with the LLM"""
    logger.info("Chatting with LLM...")
    message = await llm.ainvoke(prompt)
    if not isinstance(message.content, str):
        raise ValueError(f"Expected string, got {type(message.content)}")
    return message.content.replace("<|end|>", "").strip()


async def generate_summary(
    source: str, dest: str, template: str, quiet: bool, minimum_summary_minutes: int | None
):
    """Summarize a text file, and save it to a destination"""
    if os.path.exists(dest):
        logger.info("Summary already exists, skipping...")
        return

    with open(source, "r") as file:
        transcript_text = file.read()

    logger.info("Generating summary...")

    # Chunk size (number of characters times the estimated characters per token)
    # chunk_size = 12000 * 2
    chunk_size = 3000 * 2

    # Split the transcript text into chunks
    chunks = [
        transcript_text[i : i + chunk_size]
        for i in range(0, len(transcript_text), chunk_size)
    ]

    # List to hold summaries of each chunk
    summaries = []

    # TODO maybe replace all this with ReduceDocumentsChain?
    count = 1
    for chunk in chunks:
        print(
            f"Generating summary for chunk {count} of {len(chunks)}..."
        ) if not quiet else None
        parameters = {
            "transcript_text": chunk,
        }
        if minimum_summary_minutes is not None:
            parameters["minimum_summary_minutes"] = str(minimum_summary_minutes)
        prompt = template.format(**parameters)
        response = await chat(prompt)
        summaries.append(response)
        count += 1

    logger.info("Joining summaries, and saving...")
    combined_summary_as_yaml = "---\n" + "\n".join(summaries)
    combined_summary = yaml.safe_load(combined_summary_as_yaml)

    with open(dest, "w") as file:
        file.write(json.dumps(combined_summary, indent=2))
