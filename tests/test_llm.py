import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import llm


VTT = ""
with open("tests/fixtures/sample.vtt", "r") as file:
    VTT = file.read()


@pytest.mark.asyncio
async def test_create_transcript(monkeypatch):
    monkeypatch.setattr("os.path.exists", lambda _: False)
    monkeypatch.setattr("llm.os.makedirs", lambda _, exist_ok: None)
    monkeypatch.setattr(
        "llm.openai_client.audio.transcriptions.create",
        AsyncMock(return_value=VTT),
    )
    SAMPLE_TRANSCRIPT = [
        {"start": "00:00:01", "end": "00:00:02", "text": "Hi everybody."}
    ]
    monkeypatch.setattr("llm.convert_transcript_to_json", lambda _: SAMPLE_TRANSCRIPT)
    with patch("builtins.open") as mock_open:
        await llm.create_transcript("media_path", "dir")
        assert mock_open.call_count == 2
        mock_open.assert_any_call("media_path", "rb")
        mock_open.assert_any_call("dir/transcript.vtt", "w")
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.write.assert_any_call(VTT)


@pytest.mark.asyncio
async def test_chat():
    with patch(
        "llm.ChatOpenAI.ainvoke", return_value=MagicMock(content="content<|end|>")
    ) as mock_chat:
        response = await llm.chat("prompt")
        assert response == "content"
        assert "<|end|>" not in response
        mock_chat.assert_called_once_with("prompt")


@pytest.mark.asyncio
async def test_convert_transcript_to_json():
    json_output = llm.convert_transcript_to_json("tests/fixtures/sample.vtt")
    assert isinstance(json_output, list)
    assert len(json_output) == 5
    assert json_output[0]["start"] == "00:00:01"
    assert json_output[0]["end"] == "00:00:02"
    assert json_output[0]["text"] == "Hi everybody."
