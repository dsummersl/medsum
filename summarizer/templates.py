import concurrent.futures
import logging

from typing import List
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel,Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from .topics import split_by_dominant_topics, identify_topics


logger = logging.getLogger(__name__)


class SourceAndSummary(BaseModel):
    id: int
    topic: str = Field(description="The new topic")
    similarity: str = Field(description="How similar is the new topic to the previous one? Options: extremely similar, very similar, somewhat similar, not similar")


class Transitions(BaseModel):
    topics: List[SourceAndSummary]

# TODO https://python.langchain.com/docs/use_cases/extraction/how_to/examples -- explicitly define my own examples

TIME_TEMPLATE = """\
Transcript:

{source_text}

***

Summarize the transcript above:
- Generate a title that summarizes the content of the transcript.
- Generate two to six paragraphs in markdown summarizing the entire transcript.
- For each paragraph include all transcript source ids that are relevant.
- Use latex $$ format when referring to symbols, and equations (for instance $x=3$).
- Language should be terse, clear, and lack unnecessary words.
- Don't use words like "this transcript", or "the speaker said".

{format_instructions}

***

"""


CLIF_TEMPLATE = """\
Transcript:

{source_text}

***

Based on the transcript create an article of all topics covered, with detailed descriptions of the content:
- Identify the main topics of the transcript.
- Content can range over all the transcript source so long as its relevant to the topic at hand.
- Offer succinct yet complete overview for each section.
- Give responses in markdown.
- Use latex $ format to define equations (for instance $x=3$) and numbers.
- Define essential terms mentioned such as key individuals, theories, locations, events, and equations as markdown block quote callout blocks.
- Include an overview of any equations, diagrams that would be helpful to understand the topic.

{format_instructions}

***

"""


class Paragraph(BaseModel):
    sourceIds: List[int] = Field(
        description="source id numbers this paragragh is composed of"
    )
    markdown: str = Field(
        example="Math can be as simple as $2x^2 = 3 + 4_b$ or just **crazy** _fun_."
    )


class Topic(BaseModel):
    title: str = Field(description="A title that represents the topic.")
    summary: str = Field(
        description="A markdown formatted summarizing to the insights of a topic. "
    )
    insights: List[Paragraph] = Field(min_items=2, max_items=6)


class Article(BaseModel):
    articles: List[Topic]


time_parser = JsonOutputParser(pydantic_object=Article)
time_prompt = PromptTemplate.from_template(
    TIME_TEMPLATE,
    partial_variables={"format_instructions": time_parser.get_format_instructions()},
)

def run_with_executor(chain, chunks, use_thread_pool=True):
    if not use_thread_pool:
        return [chain(d) for d in chunks]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        return executor.map(chain, chunks)


def make_time_chain(transcript_json: List[dict]):
    # return make_newline_splitting_chain()
    def _chain(model):
        def make_source_text(items):
            return "\n".join(
                [f"id({i})|start({s['start']}) : {s['text']}" for i, s in items]
            )

        turns = identify_topics(transcript_json)
        coalesced_turn_ids = split_by_dominant_topics([t['topic'] for t in turns['transcripts']], 0.2)

        range_entries = [make_source_text(enumerate(transcript_json[r[0]:r[1]], r[0])) for r in coalesced_turn_ids]
        logger.debug("range_entries: %s", range_entries)

        all_results = []
        def process_time(chunk: str):
            return (
                {"source_text": RunnablePassthrough()}
                | time_prompt
                | model
                | time_parser
            ).invoke(chunk)

        results = run_with_executor(process_time, range_entries)

        # join together list of lists into one list
        for result in results:
            all_results.extend(result['articles'])

        return all_results

    return _chain


clif_prompt = PromptTemplate(
    template=CLIF_TEMPLATE,
    input_variables=["source_text"],
    partial_variables={"format_instructions": time_parser.get_format_instructions()},
)


def run_clif_chain(model, source_text):
    chain = time_prompt | model | time_parser
    return chain.invoke({"source_text": source_text})["topics"]


TITLE_TEMPLATE = """\
Input:

{source_text}

***

Create a title for the transcript above, and provide a summary of the input.
- Use quotes around all values in the YAML document.

{format_instructions}

***

"""


class TitleModel(BaseModel):
    title: str
    description: str


title_parser = JsonOutputParser(pydantic_object=TitleModel)

title_prompt = PromptTemplate(
    template=TITLE_TEMPLATE,
    input_variables=["source_text"],
    partial_variables={"format_instructions": title_parser.get_format_instructions()},
)


def make_title_chain(chapters_json: List[dict]):
    def _chain(model):
        chapters = "Sections:\n" + "\n".join(
            [f"{s['title']} : {s['summary']}" for s in chapters_json]
        )
        chain = title_prompt | model | title_parser
        return chain.invoke({"source_text": chapters})

    return _chain
