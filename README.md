# TLDL

_too * long * didn't * listen_ : keep the cliff notes, ditch the giant media files.

A CLI tool that summarizes audio and video files. It uses FFmpeg for processing media files and OpenAI's GPT models for generating summaries.

## Features

- Extracts compressed audio from a source media file.
- Transcribes the audio file
- Generates a summary of the transcription
- Creates snapshots for video files at key moments.
- Packages it all up in a pretty HTML viewer 🌟.

## Development

```bash
poetry shell
poetry install

python summarizer/summarizer.py --help

# install locally:
poetry install
```

## Usage

To use Media Summarizer, run the following command:

```bash
tldl [OPTIONS] SOURCE_FILE
```

### Examples

Summarize an audio file:

```bash
tldl summarize /path/to/audio.mp3

# what you get:
audio/index.html
audio/audio.html
audio/summary.json
audio/snapshots/index.html
audio/snapshots/*.jpg (lots of snapshots)
audio/transcript.vtt
audio/audio.mp3

tldl summarize /path/to/audio_and_video.mp4
# what you get:
audio_and_video/index.html
audio_and_video/audio_and_video.html
audio_and_video/summary.json
audio_and_video/snapshots/index.html
audio_and_video/snapshots/00_00_05.jpg
audio_and_video/snapshots/00_01_12.jpg
audio_and_video/transcript.vtt
audio_and_video/audio.mp3

```

Don't like the summary? - tweak any files in the summary directory regenerate
the HTML:

```sh
tldl update-index /path/to/summary-directory
```

# More Ideas

- Make the transcript and summary filterable (maybe semantically, even).
- Have some basic player options - automatically play when you click on a
    section, show the snapshots hover and automatically transition to them if the
    player is playing.
- Add an option to refine the prompt instructions.
- Add a timestamp option to the HTML so you can jump to a specific spot (or bookmark)
- Add an option to ignore video on video files.
- Add a summary of the summary to the top of the HTML report.
- Make formal metadata files so that presentation is cleanly separated from UX.
- Extract metadata from snapshots, so that its searchable.
- Improve the image snapshots - currently..._way_ too limited.
- TODO use non-openai or at least make it configurable.
- support markdown and katex: https://www.npmjs.com/package/marked-katex-extension

# Limitations

- Audio currently isn't chunked to 25mb
