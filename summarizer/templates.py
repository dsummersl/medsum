SUMMARY_TEMPLATE = """\
Transcript:
{transcript_text}
***
Please create a list that summarizes the topics discussed and parties involved in the transcript above, adhering to the following guidelines:
- Each summary should cover a minimum time interval of {minimum_summary_minutes} minutes.
- Capture topics briefly, focusing only on key points or issues.
- Key points are those frequently mentioned in the discussion, or key decisions that were made.
- Include names of people, places, or times that are mentioned in the transcript, or can be inferred from the context.
- Highlight topics, key points, and people, places, and times with a <mark> tag.

Format the output as follows:
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
      Started the agenda: <b>vacation planning</b>, <b>action items</b>.
    </li>
  </ul>
</div>
<div data-start="00:05:05">
  <b>00:05:05</b>
  <ul>
    <li>Started talking about <b>vacation planning</b>.</li>
    <li>
      Jerry discussed what kind of socks, pants and shoes should be brought.
    </li>
    <li>Sheryll brought up the idea of bringing a tent.</li>
    <li><mark>Decided to bring a tent, and personal items</mark>.</li>
  </ul>
</div>
<div data-start="00:08:13">
  <b>00:08:13</b>
  <ul>
    <li>Started talking about <b>action items</b></li>
    <li>
      People expressed a need to
      <mark>have another meeting after vacation</mark>.
    </li>
  </ul>
</div>
***
"""
