import pytest
from summarizer.topics import split_by_dominant_topics


@pytest.mark.parametrize(
    "topics, threshold, expected",
    [
        ([4, 2, 1, 1, 2, 0, 2, 4, 2, 0, 1, 3, 3, 1, 3, 3, 4], 0.20, [[0, 3], [4, 4], [5, 16]]),
        ([1, 1, 1, 2, 2, 3, 3, 3, 3], 0.33, [[0, 1], [2, 8]]),
        ([1, 2, 2, 3, 3, 1, 3, 3, 1], 0.33, [[0, 5], [6, 8]]),
        ([1, 1, 1, 4, 5], 0.50, [[0, 4]]), # only one topic, then it should be the only group
        ([1, 2, 3, 4, 5], 0.50, [[0, 4]]), # no dominant topic, should be the only group
        ([], 0.20, []),
    ]
)
def test_split_by_dominant_topics(topics, threshold, expected):
    result = split_by_dominant_topics(topics, threshold)
    assert result == expected
