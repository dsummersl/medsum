import pytest
from unittest.mock import patch, MagicMock
import llm

async def test_create_transcript():
    with patch('os.path.exists', return_value=False), \
         patch('openai.AsyncOpenAI.audio.transcriptions.create', return_value='transcript'), \
         patch('os.makedirs'), \
         patch('builtins.open', new_callable=MagicMock) as mock_open:
        await llm.create_transcript('media_path', 'dir')
        mock_open.assert_called_once_with('dir/transcript.vtt', 'w')
        mock_open().write.assert_called_once_with('transcript')

async def test_chat():
    with patch('llm.ChatOpenAI.ainvoke', return_value=MagicMock(content='content<|end|>')) as mock_chat:
        response = await llm.chat('prompt')
        assert response == 'content'
        assert '<|end|>' not in response
        mock_chat.assert_called_once_with('prompt')

async def test_generate_summary():
    with patch('os.path.exists', return_value=False), \
         patch('builtins.open', new_callable=MagicMock) as mock_open, \
         patch('llm.chat', return_value='summary') as mock_chat:
        await llm.generate_summary('source', 'dest', 'template', False)
        mock_open.assert_called_once_with('source', 'r')
        mock_chat.assert_called()
        mock_open().write.assert_called()
