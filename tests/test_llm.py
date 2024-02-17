import pytest
from unittest.mock import call, patch, MagicMock, AsyncMock
import llm

VTT = """\
WEBVTT

00:01.500 --> 00:02.200
Hi everybody.

00:02.200 --> 00:07.166
This is a quick overview on how
we're going to do Color Wheel Part One.

00:07.166 --> 00:08.833
So there are two parts of this test.

00:08.833 --> 00:11.633
They're basically variations
on the same thing, but we split it up into

00:11.633 --> 00:12.433
two separate parts.
"""

@pytest.mark.asyncio
async def test_create_transcript(monkeypatch):
    monkeypatch.setattr('os.path.exists', lambda _: False)
    monkeypatch.setattr('llm.os.makedirs', lambda _, exist_ok: None)
    transcript_mock = MagicMock(text=VTT)
    monkeypatch.setattr('llm.openai_client.audio.transcriptions.create', AsyncMock(return_value=transcript_mock))
    with patch('builtins.open') as mock_open:
        await llm.create_transcript('media_path', 'dir')
        assert mock_open.call_count == 2
        mock_open.assert_any_call('media_path', 'rb')
        mock_open.assert_any_call('dir/transcript.json', 'w')
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.write.assert_called_once_with(transcript_mock.text)

@pytest.mark.asyncio
async def test_chat():
    with patch('llm.ChatOpenAI.ainvoke', return_value=MagicMock(content='content<|end|>')) as mock_chat:
        response = await llm.chat('prompt')
        assert response == 'content'
        assert '<|end|>' not in response
        mock_chat.assert_called_once_with('prompt')
from webvtt import WebVTT

@pytest.mark.asyncio
async def test_convert_transcript_to_json():
    json_output = llm.convert_transcript_to_json(VTT)
    assert isinstance(json_output, dict)
    assert "transcript" in json_output
    assert len(json_output["transcript"]) == 4  # Number of captions in the VTT example
    assert json_output["transcript"][0]["start"] == 1.5
    assert json_output["transcript"][0]["end"] == 2.2
    assert json_output["transcript"][0]["text"] == "Hi everybody."
from webvtt import WebVTT

@pytest.mark.asyncio
async def test_convert_transcript_to_json():
    json_output = llm.convert_transcript_to_json(VTT)
    assert isinstance(json_output, dict)
    assert "transcript" in json_output
    assert len(json_output["transcript"]) == 4  # Number of captions in the VTT example
    assert json_output["transcript"][0]["start"] == 1.5
    assert json_output["transcript"][0]["end"] == 2.2
    assert json_output["transcript"][0]["text"] == "Hi everybody."
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_convert_transcript_to_json():
    json_output = llm.convert_transcript_to_json(VTT)
    assert isinstance(json_output, dict)
    assert "transcript" in json_output
    assert len(json_output["transcript"]) == 4  # Number of captions in the VTT example
    assert json_output["transcript"][0]["start"] == 1.5
    assert json_output["transcript"][0]["end"] == 2.2
    assert json_output["transcript"][0]["text"] == "Hi everybody."
