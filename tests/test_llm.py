import pytest
from unittest.mock import patch, MagicMock
from summarizer import llm

def test_create_transcript():
    with patch('os.path.exists', return_value=False), \
         patch('openai.AsyncOpenAI.audio.transcriptions.create', return_value='transcript'), \
         patch('os.makedirs'), \
         patch('builtins.open', new_callable=MagicMock):
        llm.create_transcript('media_path', 'dir')
        # Add assertions here to verify the behavior

def test_chat():
    with patch('llm.ChatOpenAI.ainvoke', return_value=MagicMock(content='content')):
        response = llm.chat('prompt')
        assert response == 'content'
        # Add more assertions here to verify the behavior

def test_generate_summary():
    with patch('os.path.exists', return_value=False), \
         patch('builtins.open', new_callable=MagicMock), \
         patch('llm.chat', return_value='summary'):
        llm.generate_summary('source', 'dest', 'template', False)
        # Add assertions here to verify the behavior
