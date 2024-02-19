from typing import List
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser


TIME_TEMPLATE = """\
Transcript:

{source_text}

***

Given the transcript and the timestamp of images (if available), identify any significant changes in the conversation and topics discussed.
- A section should summarize the topics of the time period.
- Mention key who/what/where in all description fields.
- Each summary section should summarize AT LEAST one entry of the transcript and aim to include multiple entries where relevant.
- The description of each section should account for all the summaries included in that section, providing an overview that encompasses all key points.
- Use only the timestamps provided in the transcript for the start values in the summaries.

{format_instructions}

***

"""

CLIF_TEMPLATE = """\
Transcript:

{source_text}

***

Based on the transcript create an article of all topics covered in the transcript, with detailed descriptions of the content:
- Identify the main topics of the transcript.
- For each topic:
    - Highlight essential concepts, theories, and developments discussed in each segment.
    - Include essential details such as key individuals, locations, and events.
    - Offer succinct yet complete overview, with an introduction and conclusion for each section.
    - Give responses in markdown. Use latex $ format for equations and numbers with units.
    - Use ```mermaid ``` code blocks if making a diagram.

{format_instructions}

***

"""

class Paragraph(BaseModel):
    sourceIds: List[int] = Field(description="What source id numbers this paragragh is composed of")
    markdown: str = Field(description="A formatted paragraph.")

class Topic(BaseModel):
    title: str = Field(description="A title that represents the topic.")
    introduction: str = Field(description="A markdown formatted introduction to the paragraphs of a section. ")
    paragraphs: List[Paragraph]
    conclusion: str = Field(description="A markdown formatted conclusion of the paragraphs of a section. ")

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
    results = chain.invoke({"source_text": source_text})['topics']
    for section in results:
        for summary in section['summaries']:
            summary['markdown'] = ' * ' + summary['markdown']
    return results

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
