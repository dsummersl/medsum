import logging
import os
import yaml
import json

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


def convert_transcript_to_json(transcript: str) -> dict:
    pass


async def create_transcript(media_path: str, dir: str):
    """Use openai speech-to-text to extract audio, and save it to 'dir/transcript.json'"""
    if os.path.exists(f"{dir}/transcript.json"):
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
            f.write(transcript.text)
        logger.info("Transcript saved!")

    with open(f"{dir}/transcript.json", "w") as f:
        f.write(json.dumps(convert_transcript_to_json(transcript)))


async def chat(prompt: str) -> str:
    """Chat with the LLM"""
    logger.info("Chatting with LLM...")
    message = await llm.ainvoke(prompt)
    if not isinstance(message.content, str):
        raise ValueError(f"Expected string, got {type(message.content)}")
    return message.content.replace("<|end|>", "").strip()


async def generate_summary(
    source: str, dest: str, template: str, quiet: bool, minimum_summary_minutes: int | None = None, source_in_all_prompts: str | None = None
):
    """Summarize a text file, and save it to a destination"""
    if os.path.exists(dest):
        logger.info("Summary already exists, skipping...")
        return

    with open(source, "r") as file:
        source_text = file.read()

    source_in_all_prompts_text = ""
    if source_in_all_prompts and os.path.exists(source_in_all_prompts):
        source_in_all_prompts_text = open(source_in_all_prompts, "r").read()

    logger.info("Generating summary...")

    if len(source_in_all_prompts_text) > CHUNK_SIZE:
        logger.warning(
            f"source_in_all_prompts_text is too long (not using): {len(source_in_all_prompts_text)}"
        )
        source_in_all_prompts_text = ""

    # Split the transcript text into chunks
    chunks = [
        source_in_all_prompts_text + source_text[i : i + CHUNK_SIZE]
        for i in range(0, len(source_text), CHUNK_SIZE - len(source_in_all_prompts_text))
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
            "source_text": chunk,
        }
        if minimum_summary_minutes is not None:
            parameters["minimum_summary_minutes"] = str(minimum_summary_minutes)
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
