# Media Summarizer

Media Summarizer is a simple CLI tool for summarizing text from audio and video files. It uses FFmpeg for processing media files and OpenAI's GPT models for generating summaries.

## Features

- Extracts compressed audio from a source media file.
- Transcribes the audio file
- Generates a summary of the transcription
- Creates snapshots from video files at specified timestamps.
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
medsum [OPTIONS] SOURCE_FILE
```

### Examples

Summarize an audio file:

```bash
medsum /path/to/audio.mp3
medsum /path/to/audio_and_video.mp4
```

# More Ideas

- Surface the transcript.vtt in some way.
- Make the transcript and summary searchable (maybe semantically, even).
- Let the user supply a transcript file (save $ when possible)
- Adding an option to specify the minimum interval to capture images from
    videos. Possibly filtering out adjacent snapshots that are identical or 90%
    so.
- Have some basic player options - automatically play when you click on a
    section, show the snapshots hover and automatically transition to them if the
    player is playing.

# Limitations

- Audio currently isn't chunked to 25mb
- Currently stops the player when you are playing and jump to another section.
