SUMMARY_TEMPLATE = """\
{source_text}

***

Given the transcript and the timestamp of images (if available). Identify any
significant changes in the conversation and topics discussed.
- A section should summarize the topics of the time period, focusing only on key points or issues.
- Mention key who/what/where in summaries.
- Each summary section should summarize AT LEAST one entry of the transcript.

Template of the YAML output:

- title: "[Section name]"
  description: "[Summary of the section]"
  summaries:
  - start: "[hour]:[minute]:[second]"
    title: "[Summary title]"
    description: |
      [Extended summary description]
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
