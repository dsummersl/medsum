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

Template of the YAML output:

- title: "[Section name]"
  description: "[Summary of the section, covering all included summaries]"
  summaries:
  - start: "[hour]:[minute]:[second]"
    title: "[Summary #1 title]"
    description: |
      [Extended summary #1 description]
  - start: "[hour]:[minute]:[second]"
    title: "[Summary #2 title]"
    description: |
      [Extended summary #2 description]
... more entries...

***

"""


TITLE_TEMPLATE = """\
Input:
{source_text}

***

Create a title for the transcript above, and provide a summary of the input.

Template of the output YAML format:

title: "[Title of the transcript]"
description: "[Summary]"

***

"""
