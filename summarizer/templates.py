from typing import List
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser


SUMMARY_TEMPLATE = """\
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

class SummaryItem(BaseModel):
    start: str = Field(pattern=r'^\d{2}:\d{2}:\d{2}$')
    title: str
    description: str

class SectionItem(BaseModel):
    title: str
    description: str
    summaries: List[SummaryItem]

class SummaryModel(BaseModel):
    sections: List[SectionItem]

summary_parser = JsonOutputParser(pydantic_object=SummaryModel)

summary_prompt = PromptTemplate(
    template=SUMMARY_TEMPLATE,
    input_variables=["source_text"],
    partial_variables={"format_instructions": summary_parser.get_format_instructions()},
)

def run_summary_chain(model, source_text):
    chain = summary_prompt | model | summary_parser
    results = chain.invoke({"source_text": source_text})['sections']
    for section in results:
        for summary in section['summaries']:
            summary['description'] = ' * ' + summary['description']
    return results


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
