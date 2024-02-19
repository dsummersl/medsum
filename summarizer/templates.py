from typing import List
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser


TIME_TEMPLATE = """\
Transcript:

{source_text}

***

Based on the transcript create summary of all topics covered, with detailed descriptions of the content:
- Identify the main topics discussed in the transcript, grouped by the time period of the conversation.
- For each topic:
    - Offer succinct introduction and conclusion for each topic.
    - Mention key who/what/where of the content.
    - Each summary section should summarize AT LEAST one entry of the transcript and aim to include multiple entries where relevant.
- Language should be terse, clear, and lacking all unnecessary words.

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
- For each topic:
    - Highlight essential concepts, theories, and developments discussed in each topic.
    - Include essential details such as key individuals, locations, and events.
    - Offer succinct yet complete overview, with an introduction and conclusion for each section.
    - Give responses in markdown. Use latex $ format for equations and numbers with units.
    - Use ```mermaid ``` code blocks if making a diagram.
    - Include an overview of any equations, diagrams that would be helpful to understand the topic.
- Language should be terse, clear, and lacking all unnecessary words.

{format_instructions}

***

"""

class Paragraph(BaseModel):
    sourceIds: List[int] = Field(description="What source id numbers this paragragh is composed of")
    markdown: str = Field(description="A formatted paragraph.")

class Topic(BaseModel):
    title: str = Field(description="A title that represents the topic.")
    introduction: str = Field(description="A markdown formatted introduction to the paragraphs of a topic. ")
    paragraphs: List[Paragraph]
    conclusion: str = Field(description="A markdown formatted conclusion of the paragraphs of a topic. ")

class Article(BaseModel):
    topics: List[Topic]

summary_parser = JsonOutputParser(pydantic_object=Article)

time_prompt = PromptTemplate(
    template=TIME_TEMPLATE,
    input_variables=["source_text"],
    partial_variables={"format_instructions": summary_parser.get_format_instructions()},
)

def run_time_chain(model, source_text):
    chain = time_prompt | model | summary_parser
    return chain.invoke({"source_text": source_text})['topics']


clif_prompt = PromptTemplate(
    template=CLIF_TEMPLATE,
    input_variables=["source_text"],
    partial_variables={"format_instructions": summary_parser.get_format_instructions()},
)

def run_clif_chain(model, source_text):
    chain = time_prompt | model | summary_parser
    return chain.invoke({"source_text": source_text})['topics']


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
