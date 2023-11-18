# Media Summarizer

Media Summarizer is a simple Python tool for summarizing text from audio and video files. It uses FFmpeg for processing media files and OpenAI's GPT models for generating summaries.

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
