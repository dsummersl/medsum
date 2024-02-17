import pytest
from unittest.mock import call, patch, MagicMock, AsyncMock
import llm

@pytest.mark.asyncio
async def test_create_transcript(monkeypatch):
    monkeypatch.setattr('os.path.exists', lambda _: False)
    monkeypatch.setattr('llm.os.makedirs', lambda _, exist_ok: None)
    monkeypatch.setattr('llm.openai_client.audio.transcriptions.create', AsyncMock(return_value='llm-result'))
    with patch('builtins.open') as mock_open:
        await llm.create_transcript('media_path', 'dir')
        assert mock_open.call_count == 2
        mock_open.assert_any_call('media_path', 'rb')
        mock_open.assert_any_call('dir/transcript.vtt', 'w')
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.write.assert_called_once_with('llm-result')

@pytest.mark.asyncio
async def test_chat():
    with patch('llm.ChatOpenAI.ainvoke', return_value=MagicMock(content='content<|end|>')) as mock_chat:
        response = await llm.chat('prompt')
        assert response == 'content'
        assert '<|end|>' not in response
        mock_chat.assert_called_once_with('prompt')
