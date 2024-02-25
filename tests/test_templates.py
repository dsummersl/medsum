import json
import pytest
from summarizer.templates import make_time_chain
from langchain_community.llms.fake import FakeListLLM
from summarizer.templates import make_time_chain, coalesce_similar_ids


def test_coalesce_similar_ids():
    # Mock turns with varying levels of similarity
    turns = [
        {"id": 0, "topic": "Intro", "similarity": "extremely similar"},
        {"id": 1, "topic": "Intro Continued", "similarity": "extremely similar"},
        {"id": 2, "topic": "Main Content", "similarity": "not similar"},
        {"id": 3, "topic": "Main Content Continued", "similarity": "very similar"},
        {"id": 4, "topic": "Conclusion", "similarity": "not similar"},
    ]

    # Expected coalesced IDs after processing
    expected_coalesced_ids = [0, 2, 4]

    # Coalesce the similar IDs
    coalesced_ids = coalesce_similar_ids(turns)

    # Assert that the coalesced IDs match the expected output
    assert coalesced_ids == expected_coalesced_ids


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
