import json
import pytest
from summarizer.templates import make_time_chain
from langchain_community.llms.fake import FakeListLLM


@pytest.fixture
def mock_model():
    model = FakeListLLM(
        responses=[
            json.dumps(
                {
                    "topics": [
                        {"id": 0, "topic": "Intro", "similarity": "extremely similar"},
                        {"id": 1, "topic": "Main Content", "similarity": "not similar"},
                        {"id": 2, "topic": "Conclusion", "similarity": "very similar"},
                    ]
                }
            ),
            json.dumps(
                {
                    "articles": [
                        {
                            "title": "Introduction",
                            "summary": "Hello world.",
                            "insights": [
                                {"sourceIds": [0], "markdown": "Hello world."}
                            ],
                        }
                    ],
                }
            ),
        ]
    )
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
            "insights": [{"markdown": "Hello world.", "sourceIds": [0]}],
        }
    ]

    # Assert that the result matches the expected output
    assert result == expected_output
