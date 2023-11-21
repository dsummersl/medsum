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

<div data-start="[hour]:[minute]:[second]">
  <b>[hour]:[minute]:[second]</b>
  <ul>
    <li>[Summary entry]</li>
  </ul>
</div>

Example:
<div data-start="00:03:15">
  <b>00:03:15</b>
  <ul>
    <li>
      Started the agenda: <mark>vacation planning</mark>, <mark>action items</mark>.
    </li>
  </ul>
</div>
<div data-start="00:05:05">
  <b>00:05:05</b>
  <ul>
    <li>Started talking about <mark>vacation planning</mark>.</li>
    <li>
      <mark>Jerry</mark> discussed what kind of socks, pants and shoes should be brought.
    </li>
    <li><mark>Sheryll</mark> brought up the idea of bringing a tent.</li>
    <li><mark>Decided to bring a tent, and personal items</mark>.</li>
  </ul>
</div>
<div data-start="00:08:13">
  <b>00:08:13</b>
  <ul>
    <li>Started talking about <mark>action items</mark></li>
    <li>
      People expressed a need to <mark>have another meeting after vacation</mark>.
    </li>
  </ul>
</div>

***

"""
