SUMMARY_TEMPLATE = """\
Transcript:
{transcript_text}

***

Summarize the topics discussed and parties involved in the transcript above with the following guidelines:
- Organize the summary into sections. Each section should start immediately after the previous one ends, with no overlaps or gaps.
- A section should summarize the topics of the time period, focusing only on key points or issues.
- Key points are those frequently mentioned in the discussion, or key decisions that were made.
- Highlight people, places, things, topics, key points, and times that are mentioned.
- Use a <mark> tag to highlight.
- Each section should cover at least a {minimum_summary_minutes} minute period.
- Avoid creating sections with only one entry (they should have multiple entries where possible)

Template of the output format:

- start: "[hour]:[minute]:[second]"
  title: "[Summary title]"
  description: |
    [Extended summary description]
... more summary entries...

Example:

- start: "00:03:15"
  title: "Vacation Planning"
  description: |
    Started a discussion about vacation planning. Jerry discussed what kind of
    socks, pants and shoes should be brought. Sheryll brought up the idea of
    bringing a tent. Decided to bring a tent, and personal items.
- start: "00:08:13"
  title: "Action Items"
  description: |
    The vacation planning stopped and the group decided to take a tent, and some
    basic personal items. Everyone expressed a need to have another meeting
    after vacation.

***

"""


CHAPTERS_TEMPLATE = """\
Input:
{transcript_text}

***

Group the entries above into chapters:
- Provide a title, and a summary of the sections that were grouped together.
- Group at least three sections together.

Template of the output YAML format:

- start: "[hour]:[minute]:[second]"
  title: "[Section summary]"
  description: "[Longer description]"
... more summary entries...

Example:

- start: "00:03:15"
  title: "Overview of the camping trip."
  description: |
    The group discussed the a camping trip to Novia Scotia. They talked about
    where it would be and then what kinds of things they thouht they'd want to
    bring.
- start: "00:38:03"
  title: "Summary and end of meeting"
  description: |
    Some people had left earlier, so they decided to send an email about the
    decisions that were made. They decided to meet again in a week to finalize
    the plans.

***

"""


TITLE_TEMPLATE = """\
Input:
{transcript_text}

***

Create a title for the transcript above, and provide a summary of the input.

Template of the output YAML format:

title: "[Title of the transcript]"
description: "[Summary]"
duration: "[hour]:[minute]:[second]"

***

"""
