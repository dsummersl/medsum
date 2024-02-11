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


TOPIC_SHIFT_TEMPLATE = """\
Transcript:
{transcript_text}

***

Identify the subsections within the transcript that correspond to the topic
shifts.
- Provide a brief summary or description of each subsection.
- Key points are those frequently mentioned in the discussion, or key decisions that were made.
- Highlight people, places, things, topics, key points, and times that are mentioned.
- Use a <mark> tag to highlight.

Template of the output YAML format:

- start: "[hour]:[minute]:[second]"
  text: "[Summary entry]"
... more summary entries...

Example:

- start: "00:03:15"
  text: "Started talking about <mark>action items</mark>"
- start: "00:05:38"
  text: "<mark>Sheryll</mark> brought up the idea of bringing a tent."

***

"""
