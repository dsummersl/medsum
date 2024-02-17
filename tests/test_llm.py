import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import llm

@pytest.mark.asyncio
async def test_create_transcript(monkeypatch):
    monkeypatch.setattr('os.path.exists', lambda _: False)
    monkeypatch.setattr('llm.os.makedirs', lambda _, exist_ok: None)
    monkeypatch.setattr('llm.openai_client.audio.transcriptions.create', AsyncMock(return_value='llm-result'))
    def side_effect(*args, **kwargs):
        if args[0] == 'media_path' and args[1] == 'rb':
            return MagicMock()
        elif args[0] == 'dir/transcript.vtt' and args[1] == 'w':
            return MagicMock()
        else:
            raise ValueError("Unexpected arguments!")

    with patch('builtins.open', new_callable=MagicMock, side_effect=side_effect) as mock_open:
        await llm.create_transcript('media_path', 'dir')
        mock_open.assert_called_once_with('media_path', 'rb')
        mock_open.assert_called_once_with('dir/transcript.vtt', 'w')
        mock_open().write.assert_called_once_with('llm-result')

@pytest.mark.asyncio
async def test_chat():
    with patch('llm.ChatOpenAI.ainvoke', return_value=MagicMock(content='content<|end|>')) as mock_chat:
        response = await llm.chat('prompt')
        assert response == 'content'
        assert '<|end|>' not in response
        mock_chat.assert_called_once_with('prompt')

@pytest.mark.asyncio
async def test_generate_summary():
    with patch('os.path.exists', return_value=False), \
         patch('builtins.open', new_callable=MagicMock) as mock_open, \
         patch('llm.chat', return_value='summary') as mock_chat:
        await llm.generate_summary('source', 'dest', 'template', False)
        mock_open.assert_called_once_with('source', 'r')
        mock_chat.assert_called()
        mock_open().write.assert_called()
