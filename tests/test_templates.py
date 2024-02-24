import pytest
from unittest.mock import Mock
from summarizer.templates import make_time_chain


@pytest.fixture
def mock_model():
    model = Mock()
    model.return_value = {
        "topics": [
            {"id": 0, "topic": "Introduction", "similarity": "extremely similar"},
            {"id": 1, "topic": "Main Content", "similarity": "not similar"},
            {"id": 2, "topic": "Conclusion", "similarity": "very similar"},
        ]
    }
    return model


def test_make_time_chain(mock_model):
    # Mock transcript JSON
    transcript_json = [
        {"start": "00:00:01", "text": "Hello world."},
        {"start": "00:00:05", "text": "This is a test."},
        {"start": "00:00:10", "text": "Another sentence."},
    ]

    # Create the time chain
    time_chain = make_time_chain(transcript_json)

    # Run the time chain with the mock model
    result = time_chain(mock_model)

    # Expected output
    expected_output = [
        {
            "title": "Introduction",
            "summary": "Hello world.",
            "insights": [{"sourceIds": [0], "markdown": "Hello world."}],
        },
        {
            "title": "Main Content",
            "summary": "This is a test.",
            "insights": [{"sourceIds": [1], "markdown": "This is a test."}],
        },
        {
            "title": "Conclusion",
            "summary": "Another sentence.",
            "insights": [{"sourceIds": [2], "markdown": "Another sentence."}],
        },
    ]

    # Assert that the result matches the expected output
    assert result == expected_output
