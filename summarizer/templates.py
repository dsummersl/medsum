import concurrent.futures
import logging

from typing import List
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel


import pdb


logger = logging.getLogger(__name__)


TURNS_TEMPLATE = """\
Transcript:

{source_text}

***

In the transcript above identify which transcript ids in the transcript mark a
place where the topic changes. Score this transition: how similar is the new
topic to the previous one?

{format_instructions}

***

"""


class SourceAndSummary(BaseModel):
    id: int
    topic: str = Field(description="The new topic")
    similarity: str = Field(description="How similar is the new topic to the previous one? Options: extremely similar, very similar, somewhat similar, not similar")


class Transitions(BaseModel):
    topics: List[SourceAndSummary]


TIME_TEMPLATE = """\
Transcript:

{source_text}

***

Based on the transcript above group it by its common topic and summarize:
- Identify the loose topic of the cluster of entries, and generate an introductory summary.
- For each cluster of entries create an insightful summary for each of the following:
  - Each individuals referenced, and their role in the topic.
  - Times or events mentioned in the topic
  - Locations or places mentioned in the topic
  - Things or objects mentioned in the topic
  - Ideas, definitions, or theories mentioned in the topic
- Use markdown latex format when referring to symbols, and equations (for instance $x=3$).
- Language should be terse, clear, and lack unnecessary words.
- The entire range of transcript entries should be accounted for in the output. Every transcript entry should be part of a cluster.

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
        description="What source id numbers this paragragh is composed of"
    )
    markdown: str = Field(
        description="A markdown formatted paragraph, possibly with katex definitions."
    )


class Topic(BaseModel):
    title: str = Field(description="A title that represents the topic.")
    summary: str = Field(
        description="A markdown formatted summarizing to the insights of a topic. "
    )
    insights: List[Paragraph]


class Article(BaseModel):
    articles: List[Topic]


summary_parser = JsonOutputParser(pydantic_object=Article)

time_prompt = PromptTemplate(
    template=TIME_TEMPLATE,
    input_variables=["source_text"],
    partial_variables={"format_instructions": summary_parser.get_format_instructions()},
)

turns_parser = JsonOutputParser(pydantic_object=Transitions)
turns_prompt = PromptTemplate.from_template(
    TURNS_TEMPLATE,
    partial_variables={"format_instructions": turns_parser.get_format_instructions()},
)


def coalesce_similar_ids(turns):
    if len(turns) == 0:
        return []

    # When the similarity field contains 'extremely' or 'very' we'll
    # coalesce them together with the previous turn
    coalesced_turn_ids = []
    for turn in turns:
        is_similar = ('extremely' in turn['similarity'] or 'very' in turn['similarity'])
        if not is_similar or len(coalesced_turn_ids) == 0:
            coalesced_turn_ids.append(turn['id'])
    return coalesced_turn_ids


def make_time_chain(transcript_json: List[dict]):
    def _chain(model):
        splitter = CharacterTextSplitter("\n")

        def make_source_text(items):
            return "\n".join(
                [f"id({i})|start({s['start']}) : {s['text']}" for i, s in items]
            )

        def process_chunk(chunk: Document):
            turns_chain = (
                {"source_text": RunnablePassthrough()}
                | turns_prompt
                | model
                | turns_parser
            )
            return turns_chain.invoke(chunk)

        turns = []
        documents = splitter.split_text(make_source_text(enumerate(transcript_json)))
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(
                    process_chunk,
                    documents)

            # join together list of lists into one list
            for result in results:
                turns.extend(result['topics'])

        coalesced_turn_ids = coalesce_similar_ids(turns)

        # For turns we need to
        # - create a list of ranges from the turns. For instance if we have
        #   [ 0, 7, 22, 38 ]
        #   then we need to create
        #   [ (0, 7), (7, 22), (22, 38) ]
        turn_ids = [t for t in coalesced_turn_ids]
        ranges = list(zip(turn_ids, turn_ids[1:]))

        all_results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(
                    process_chunk,
                    [transcript_json[r[0]:r[1]] for r in ranges])

            # join together list of lists into one list
            for result in results:
                all_results.extend(result['articles'])

        return all_results

    return _chain


clif_prompt = PromptTemplate(
    template=CLIF_TEMPLATE,
    input_variables=["source_text"],
    partial_variables={"format_instructions": summary_parser.get_format_instructions()},
)


def run_clif_chain(model, source_text):
    chain = time_prompt | model | summary_parser
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


def run_title_chain(model, source_text):
    chain = title_prompt | model | title_parser
    return chain.invoke({"source_text": source_text})
