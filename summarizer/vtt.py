import os
import re


def time_string_to_seconds(time_string):
    """
    Converts a time string in "hh:mm" or "hh:mm:ss.ddd" format to seconds.

    :param time_string: String representing the time.
    :return: Time in seconds as a float.
    """
    parts = time_string.split(':')

    if len(parts) == 2:  # hh:mm format
        hours, minutes = parts
        seconds = 0
    elif len(parts) == 3:  # hh:mm:ss.ddd format
        hours, minutes, sec_part = parts
        seconds = sec_part.partition('.')[0]
    else:
        raise ValueError("Invalid time format")

    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def extract_transcript_start_times(dir: str):
    """
    Extracts start times from a VTT file.

    :param vtt_path: Path to the VTT file.
    :return: List of start times in seconds.
    """
    vtt_path = os.path.join(dir, "transcript.vtt")

    start_times = []
    time_pattern = re.compile(
        r"^(\d{2}:\d{2}:\d{2}).\d{3} --> \d{2}:\d{2}:\d{2}.\d{3}$"
    )
    with open(vtt_path, "r") as file:
        for line in file:
            match = time_pattern.search(line)
            if match:
                start_times.append(match.group(1))
    return start_times


