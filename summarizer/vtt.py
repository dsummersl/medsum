import os
import re


def time_string_to_seconds(time_string):
    """
    Converts a time string in "hh:mm", "hh:mm:ss.ddd", "mm:ss.ddd" format to seconds.

    :param time_string: String representing the time.
    :return: Time in seconds as a float.
    """
    patterns = [
        re.compile(r"^(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}).(?P<ms>\d{3})$"),
        re.compile(r"^(?P<minute>\d{2}):(?P<second>\d{2}).(?P<ms>\d{3})$"),
        re.compile(r"^(?P<hour>\d{2}):(?P<minute>\d{2})$"),
    ]

    hours = 0
    minutes = 0
    seconds = 0
    for pattern in patterns:
        match = pattern.match(time_string)
        if match:
            hours = match.groupdict().get("hour", 0)
            minutes = match.groupdict().get("minute", 0)
            seconds = match.groupdict().get("second", 0)
            break

    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def extract_transcript_start_times(dir: str):
    """
    Extracts start times from a VTT file.

    :param vtt_path: Path to the VTT file.
    :return: List of start times in seconds.
    """
    vtt_path = os.path.join(dir, "transcript.vtt")

    start_times = []
    patterns = [
        re.compile(r"^(\d{2}:\d{2}:\d{2}.\d{3}) --> \d{2}:\d{2}:\d{2}.\d{3}$"),
        re.compile(r"^(\d{2}:\d{2}.\d{3}) --> \d{2}:\d{2}.\d{3}$"),
    ]
    with open(vtt_path, "r") as file:
        for line in file:
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    start_times.append(match.group(1))
                    break
    return start_times
