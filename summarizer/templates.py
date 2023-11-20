HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Audio Transcript Summary</title>
    <style>
        body {{
            margin: 20px;
            font-family: Arial, sans-serif;
        }}

        h1 {{
            text-align: center;
        }}

        .header {{
            text-align: center;
            margin-bottom: 10px;
        }}

        .icon {{
            cursor: pointer;
            padding: 5px;
            margin-left: 5px;
            margin-right: 20px;
            user-select: none;
        }}

        #toggleTranscript {{
            position: absolute;
            top: 10px;
            right: 20px;
        }}

        .container {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }}

        .main-container {{
            display: flex;
        }}

        .summary-container {{
            flex: 1 1 66%;
        }}

        .vtt-container {{
            flex: 1 1 33%;
            white-space: pre-wrap; /* To preserve formatting of VTT file */
            display: none;
        }}

        .audio-container {{
            position: fixed;
            bottom: 20px; /* Padding from the bottom */
            left: 50%;
            transform: translateX(-50%);
        }}

        .vtt-container div {{
            font: 10px Arial, monospace;
        }}

        .vtt-container div[data-start] {{
            margin-top: 10px;
        }}

        .summary-container div[data-start] {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            transition: background-color 0.3s ease;
        }}

        .summary-container div[data-start] img {{
            flex: 1 1 33%; /* 1/3 of the container's width */
            max-width: 200px;
            height: auto;
            margin-left: auto; /* Aligns the image to the right */
        }}

        .summary-container div[data-start] > * {{
            flex: 2 1 66%; /* 2/3 of the container's width */
            margin-right: 10px;
        }}

        .summary-container div[data-start]:hover,
        .summary-container div[data-start].highlight {{
            background-color: #f0f0f0;
        }}

        div[data-start].playing {{
            background-color: #ffdab9; /* light orange */
        }}

        .zoomed-img {{
            position: fixed;
            z-index: 10;
            width: 50vw;
            height: auto;
            box-shadow: 0 0 8px rgba(0,0,0,0.5);
            display: none;
            pointer-events: none; /* Make sure it doesn't interfere with other elements */
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }}
    </style>
    <script>
        function insertImages() {{
            var summaries = document.querySelectorAll('.summary-container div[data-start]');

            summaries.forEach(function(summary) {{
                var startTime = summary.getAttribute('data-start');
                var imageName = startTimeToImageName(startTime);
                var zoomedImg = document.querySelector('.zoomed-img');

                // Create an img element and set its source
                var img = document.createElement('img');
                img.src = imageName;
                img.onerror = function() {{
                    // If the image fails to load, remove the img element
                    img.remove();
                }};
                img.onload = function() {{
                    // Insert the image above the summary div if it loads successfully
                    summary.insertBefore(img, summary.lastChild);
                }};
                // Event listeners for hover
                img.onmouseover = function() {{
                    zoomedImg.src = img.src;
                    zoomedImg.style.display = 'block';
                }};
                img.onmouseout = function() {{
                    zoomedImg.style.display = 'none';
                }};

                // Create a container for the text content
                var textContent = document.createElement('div');
                textContent.className = 'text-content';

                // Move existing children (except img) to textContent div
                Array.from(summary.childNodes).forEach(function(child) {{
                    if (child.nodeName !== 'IMG') {{
                        textContent.appendChild(child);
                    }}
                }});

                // Append the textContent div and image to the summary div
                summary.appendChild(textContent);
                summary.appendChild(img);
            }});
        }}

        function startTimeToImageName(startTime) {{
            // Assuming startTime format is 'mm:ss'
            var parts = startTime.split(':');
            var minutes = parts[0];
            var seconds = parts[1];
            return minutes + '_' + seconds + '.jpg';
        }}

        function setAudioPlayerOffset(start, summaryNumber) {{
            var audioPlayer = document.getElementById('audioPlayer');
            var source = document.getElementById('audioSource');

            var isPlaying = !audioPlayer.paused;
            source.src = './audio.mp3#t=' + start;
            audioPlayer.load();
            if (isPlaying) {{
                audioPlayer.play();
            }}

            highlightSummary(summaryNumber)
        }}

        function highlightSummary(summaryNumber) {{
            var summaries = document.querySelectorAll('.summary-container div[data-start]');
            summaries.forEach(function(div) {{
                if (div.getAttribute('data-start') === summaryNumber) {{
                    div.classList.add('playing');
                }} else {{
                    div.classList.remove('playing');
                }}
            }});
        }}

        function updateHighlightBasedOnTime() {{
            // TODO we have a bug here where the source.src = above is firing an
            // event with currentTime = 0 and then a real timer, leading to a
            // flicker on the screen.

            var audioPlayer = document.getElementById('audioPlayer');
            var currentTime = audioPlayer.currentTime;

            var summaries = document.querySelectorAll('.summary-container div[data-start], .vtt-container div[data-start]');
            summaries.forEach(function(div) {{
                var startTime = timeStringToSeconds(div.getAttribute('data-start'));
                var endTime = timeStringToSeconds(div.getAttribute('data-end'));

                if (currentTime >= startTime && currentTime < endTime) {{
                    div.classList.add('playing');
                }} else {{
                    div.classList.remove('playing');
                }}
            }});
        }}

        function preprocessVTTContent() {{
            var vttContainer = document.querySelector('.vtt-container');
            var lines = vttContainer.textContent.split('\\n');
            var processedHTML = '';

            lines.forEach(function(line) {{
                if (line.includes('-->')) {{
                    var times = line.split('-->');
                    var start = times[0].trim();
                    var end = times[1].trim();
                    processedHTML += `<div data-start="${{start}}" data-end="${{end}}">${{line}}</div>`;
                }} else {{
                    processedHTML += `<div>${{line}}</div>`;
                }}
            }});

            vttContainer.innerHTML = processedHTML;
        }}


        function timeStringToSeconds(timeString) {{
            var parts = timeString.split(':'); // Split at the colons

            var hours = 0;
            var minutes = parseInt(parts[0], 10);
            var seconds = parseInt(parts[1], 10);

            if (parts.length > 2) {{
                var secondsParts = parts[2].split('.');
                hours = parseInt(parts[0], 10);
                minutes = parseInt(parts[1], 10);
                seconds = parseInt(secondsParts[0], 10);
            }}

            return hours * 3600 + minutes * 60 + seconds;
        }}

        function toggleAllTranscripts() {{
          var transcripts = document.querySelector(".vtt-container");
          transcripts.style.display = transcripts.style.display === "block" ? "none" : "block";
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            var summaryDivs = document.querySelectorAll('div[data-start]');
            summaryDivs.forEach(function(div) {{
                div.addEventListener('click', function() {{
                  var start = this.getAttribute('data-start');
                  var summaryNumber = this.getAttribute('data-start');
                  setAudioPlayerOffset(start, summaryNumber);
                }});
            }});

            var audioPlayer = document.getElementById('audioPlayer');
            audioPlayer.addEventListener('timeupdate', updateHighlightBasedOnTime);

            document.getElementById('toggleTranscript').addEventListener('click', toggleAllTranscripts);

            insertImages();
            preprocessVTTContent();
            }});
    </script>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="search-container">
            <div class="icon" alt="Show transcript" id="toggleTranscript">📄</div>
        </div>
    </div>

    <div class="audio-container">
        <audio id="audioPlayer" controls>
            <source id="audioSource" src="./audio.mp3" type="audio/mpeg" />
            Your browser does not support the audio element.
        </audio>
    </div>

    <div class="main-container">
        <div class="container summary-container">
        {summary}
        </div>

        <pre class="container vtt-container">
        {transcript}
        </pre>
    </div>

    <img class="zoomed-img" src="" alt="">
</body>
</html>
"""

SUMMARY_TEMPLATE = """\
Transcript:
{transcript_text}
***
Create a list that summarizes topics discussed and parties involved in the transcript above.
Capture topics briefly (only highlight key points or issues).
Key points are things that were mentioned frequently in the discussion, or decisions that were made.
Include any names of people, places, or times (who, what, when) that are mentioned in the transcript, or you can be inferred by the context.
Give a response in html. Highlight key points with <mark> tags.

Use this output format:
<div data-start="[hour]:[minute]:[second]" data-end="[hour]:[minute]:[second]">
  <b>[hour]:[minute]:[second] - [hour]:[minute]:[second]</b>
  <ul>
    <li>[entry 1]</li>
    <li>[entry 2]</li>
  </ul>
</div>

Example:
<div data-start="00:00:00" data-end="00:00:10">
  <b>00:00:00 - 00:00:10</b>
  <ul>
    <li>Discussed the weather, what was happening over the weekend.</li>
  </ul>
</div>
<div data-start="00:03:15" data-end="00:05:05">
  <b>00:03:15 - 00:05:05</b>
  <ul>
    <li>
      Started the agenda: <b>vacation planning</b>, <b>action items</b>.
    </li>
  </ul>
</div>
<div data-start="00:05:05" data-end="00:08:13">
  <b>00:05:05 - 00:08:13</b>
  <ul>
    <li>Started talking about <b>vacation planning</b>.</li>
    <li>
      Jerry discussed what kind of socks, pants and shoes should be brought.
    </li>
    <li>Sheryll brought up the idea of bringing a tent.</li>
    <li><mark>Decided to bring a tent, and personal items</mark>.</li>
  </ul>
</div>
<div data-start="00:08:13" data-end="00:10:15">
  <b>00:08:13 - 00:10:15</b>
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
