import pytest
from summarizer.vtt import time_string_to_seconds, extract_transcript_start_times
from unittest.mock import mock_open, patch


@pytest.mark.parametrize("time_string, expected_seconds", [
    ("00:01", 60),
    ("01:00:00.000", 3600),
    ("00:01:02.000", 62),
    ("01:02", 3720),
])
def test_time_string_to_seconds(time_string, expected_seconds):
    assert time_string_to_seconds(time_string) == expected_seconds


def test_extract_transcript_start_times():
    mock_vtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Lorem ipsum dolor sit amet,

00:00:05.000 --> 00:00:10.000
consectetur adipiscing elit,
"""
    with patch("builtins.open", mock_open(read_data=mock_vtt_content)):
        with patch("os.path.join", return_value="transcript.json"):
            start_times = extract_transcript_start_times(".")
            assert start_times == ["00:00:00", "00:00:05"]
