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

        .container {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }}

        .summary-container {{
            border-right: 1px solid #ddd;
        }}

        .vtt-container {{
            white-space: pre-wrap; /* To preserve formatting of VTT file */
            display: none;
        }}

        .audio-container {{
            position: fixed;
            bottom: 20px; /* Padding from the bottom */
            left: 50%;
            transform: translateX(-50%);
        }}

        div[data-start] {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            transition: background-color 0.3s ease;
        }}

        div[data-start] img {{
            flex: 1 1 33%; /* 1/3 of the container's width */
            max-width: 200px;
            height: auto;
            margin-left: auto; /* Aligns the image to the right */
        }}

        div[data-start] > * {{
            flex: 2 1 66%; /* 2/3 of the container's width */
            margin-right: 10px;
        }}

          div[data-start]:hover,
        div[data-start].highlight {{
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

        function playSegment(start, summaryNumber) {{
            var audioPlayer = document.getElementById('audioPlayer');
            var source = document.getElementById('audioSource');

            source.src = './audio.mp3#t=' + start;
            audioPlayer.load();

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
            var audioPlayer = document.getElementById('audioPlayer');
            var currentTime = audioPlayer.currentTime; // Current playback time in seconds

            var summaries = document.querySelectorAll('.summary-container div[data-start]');
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

        function setupEventListeners() {{
            var summaryDivs = document.querySelectorAll('div[data-start]');
            summaryDivs.forEach(function(div) {{
                div.addEventListener('click', function() {{
                  var start = this.getAttribute('data-start');
                  var summaryNumber = this.getAttribute('data-start');
                  playSegment(start, summaryNumber);
                }});
            }});

            var audioPlayer = document.getElementById('audioPlayer');
            audioPlayer.addEventListener('timeupdate', updateHighlightBasedOnTime);

            insertImages();
        }}

        window.onload = setupEventListeners;
    </script>
</head>
<body>
    <div class="audio-container">
        <audio id="audioPlayer" controls>
            <source id="audioSource" src="./audio.mp3" type="audio/mpeg" />
            Your browser does not support the audio element.
        </audio>
    </div>

    <div class="container summary-container">
    {summary}
    </div>

    <div class="container vtt-container">
    {transcript}
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
<div data-start="[hour]:[minute]" data-end="[hour]:[minute]">
  <b>[hour]:[minute] - [hour]:[minute]</b>
  <ul>
    <li>[entry 1]</li>
    <li>[entry 2]</li>
  </ul>
</div>

Example:
<div data-start="00:00" data-end="00:10">
  <b>00:00 - 00:10</b>
  <ul>
    <li>Discussed the weather, what was happening over the weekend.</li>
  </ul>
</div>
<div data-start="03:15" data-end="05:05">
  <b>03:15 - 05:05</b>
  <ul>
    <li>
      Started the agenda: <b>vacation planning</b>, <b>action items</b>.
    </li>
  </ul>
</div>
<div data-start="05:05" data-end="08:13">
  <b>05:05 - 08:13</b>
  <ul>
    <li>Started talking about <b>vacation planning</b>.</li>
    <li>
      Jerry discussed what kind of socks, pants and shoes should be brought.
    </li>
    <li>Sheryll brought up the idea of bringing a tent.</li>
    <li><mark>Decided to bring a tent, and personal items</mark>.</li>
  </ul>
</div>
<div data-start="08:13" data-end="10:15">
  <b>08:13 - 10:15</b>
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
