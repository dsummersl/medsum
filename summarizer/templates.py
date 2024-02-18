SUMMARY_TEMPLATE = """\
{source_text}

***

Given the transcript and the timestamp of images (if available), identify any significant changes in the conversation and topics discussed.
- A section should summarize the topics of the time period, focusing only on key points or issues.
- Avoid repetitive phrases like "the speaker" in summaries. Use varied language to keep the text engaging.
- Mention key who/what/where in summaries.
- Each summary section should summarize AT LEAST one entry of the transcript and aim to include multiple entries where relevant.
- The description of each section should be comprehensive, providing an overview that encompasses all key points covered in the summaries. It should not be overly brief and should reflect the depth of the discussion.

Template of the YAML output:

- title: "[Section name]"
  description: "[Comprehensive summary of the section, covering all included summaries]"
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
