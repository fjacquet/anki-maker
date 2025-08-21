"""
Tests for the LLM client module.
"""

import pytest

from src.document_to_anki.core.llm_client import FlashcardData, LLMClient


class TestLLMClient:
    """Test cases for LLMClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = LLMClient()
    
    def test_init(self):
        """Test LLMClient initialization."""
        client = LLMClient(model="test-model", max_tokens=2000)
        assert client.model == "test-model"
        assert client.max_tokens == 2000
        assert client.max_retries == 3
        assert client.base_delay == 1.0
    
    def test_chunk_text_for_processing_short_text(self):
        """Test text chunking with short text."""
        text = "This is a short text."
        chunks = self.client.chunk_text_for_processing(text)
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_for_processing_long_text(self):
        """Test text chunking with long text."""
        # Create a text longer than max_tokens * 4 characters
        long_text = "This is a sentence. " * 1000  # ~20,000 characters
        chunks = self.client.chunk_text_for_processing(long_text, max_tokens=1000)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 4000  # max_tokens * 4
    
    def test_chunk_text_for_processing_paragraphs(self):
        """Test text chunking respects paragraph boundaries."""
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        chunks = self.client.chunk_text_for_processing(text, max_tokens=10)
        
        # Should split by paragraphs
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.strip()
    
    def test_create_flashcard_prompt(self):
        """Test flashcard prompt creation."""
        text = "Python is a programming language."
        prompt = self.client._create_flashcard_prompt(text)
        
        assert "Python is a programming language." in prompt
        assert "JSON array" in prompt
        assert "question" in prompt
        assert "answer" in prompt
        assert "card_type" in prompt
    
    def test_parse_flashcard_response_valid_json(self):
        """Test parsing valid JSON response."""
        response = '''[
            {
                "question": "What is Python?",
                "answer": "A programming language",
                "card_type": "qa"
            },
            {
                "question": "Python is a {{c1::programming language}}",
                "answer": "programming language",
                "card_type": "cloze"
            }
        ]'''
        
        flashcards = self.client._parse_flashcard_response(response)
        
        assert len(flashcards) == 2
        assert flashcards[0].question == "What is Python?"
        assert flashcards[0].answer == "A programming language"
        assert flashcards[0].card_type == "qa"
        assert flashcards[1].card_type == "cloze"
    
    def test_parse_flashcard_response_invalid_json(self):
        """Test parsing invalid JSON response with fallback."""
        response = '''
        Q: What is Python?
        A: A programming language
        
        Q: Who created Python?
        A: Guido van Rossum
        '''
        
        flashcards = self.client._parse_flashcard_response(response)
        
        assert len(flashcards) == 2
        assert flashcards[0].question == "What is Python?"
        assert flashcards[0].answer == "A programming language"
        assert flashcards[0].card_type == "qa"
    
    def test_parse_flashcard_response_missing_fields(self):
        """Test parsing response with missing required fields."""
        response = '''[
            {
                "question": "What is Python?",
                "card_type": "qa"
            },
            {
                "question": "Valid question",
                "answer": "Valid answer",
                "card_type": "qa"
            }
        ]'''
        
        flashcards = self.client._parse_flashcard_response(response)
        
        # Should skip the invalid one and keep the valid one
        assert len(flashcards) == 1
        assert flashcards[0].question == "Valid question"
    
    def test_parse_flashcard_response_invalid_card_type(self):
        """Test parsing response with invalid card_type."""
        response = '''[
            {
                "question": "What is Python?",
                "answer": "A programming language",
                "card_type": "invalid"
            }
        ]'''
        
        flashcards = self.client._parse_flashcard_response(response)
        
        assert len(flashcards) == 1
        assert flashcards[0].card_type == "qa"  # Should default to "qa"
    
    def test_fallback_parse_qa_pattern(self):
        """Test fallback parser with Q: A: pattern."""
        response = '''
        Q: What is Python?
        A: A programming language
        
        Q: Who created Python?
        A: Guido van Rossum
        '''
        
        flashcards = self.client._fallback_parse(response)
        
        assert len(flashcards) == 2
        assert flashcards[0].question == "What is Python?"
        assert flashcards[0].answer == "A programming language"
        assert flashcards[1].question == "Who created Python?"
        assert flashcards[1].answer == "Guido van Rossum"
    
    def test_fallback_parse_question_answer_pattern(self):
        """Test fallback parser with Question: Answer: pattern."""
        response = '''
        Question: What is Python?
        Answer: A programming language
        
        Question: Who created Python?
        Answer: Guido van Rossum
        '''
        
        flashcards = self.client._fallback_parse(response)
        
        assert len(flashcards) == 2
        assert flashcards[0].question == "What is Python?"
        assert flashcards[0].answer == "A programming language"
    
    def test_fallback_parse_numbered_pattern(self):
        """Test fallback parser with numbered pattern."""
        response = '''
        1. What is Python? - A programming language
        2. Who created Python? - Guido van Rossum
        '''
        
        flashcards = self.client._fallback_parse(response)
        
        assert len(flashcards) == 2
        assert flashcards[0].question == "What is Python?"
        assert flashcards[0].answer == "A programming language"
    
    @pytest.mark.asyncio
    async def test_make_api_call_with_retry_success(self, mocker):
        """Test successful API call."""
        mock_response = mocker.MagicMock()
        mock_response.choices = [mocker.MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        
        mocker.patch('litellm.completion', return_value=mock_response)
        result = await self.client._make_api_call_with_retry("test prompt")
        assert result == "Test response"
    
    @pytest.mark.asyncio
    async def test_make_api_call_with_retry_failure(self, mocker):
        """Test API call with all retries failing."""
        mocker.patch('litellm.completion', side_effect=Exception("API Error"))
        with pytest.raises(Exception, match="Failed to get response from LLM"):
            await self.client._make_api_call_with_retry("test prompt")
    
    @pytest.mark.asyncio
    async def test_make_api_call_with_retry_eventual_success(self, mocker):
        """Test API call succeeding after initial failures."""
        mock_response = mocker.MagicMock()
        mock_response.choices = [mocker.MagicMock()]
        mock_response.choices[0].message.content = "Success response"
        
        # Fail twice, then succeed
        side_effects = [Exception("Error 1"), Exception("Error 2"), mock_response]
        
        mocker.patch('litellm.completion', side_effect=side_effects)
        result = await self.client._make_api_call_with_retry("test prompt")
        assert result == "Success response"
    
    @pytest.mark.asyncio
    async def test_generate_flashcards_from_text_empty(self):
        """Test generating flashcards from empty text."""
        result = await self.client.generate_flashcards_from_text("")
        assert result == []
        
        result = await self.client.generate_flashcards_from_text("   ")
        assert result == []
    
    @pytest.mark.asyncio
    async def test_generate_flashcards_from_text_success(self, mocker):
        """Test successful flashcard generation."""
        mock_response = mocker.MagicMock()
        mock_response.choices = [mocker.MagicMock()]
        mock_response.choices[0].message.content = '''[
            {
                "question": "What is Python?",
                "answer": "A programming language",
                "card_type": "qa"
            }
        ]'''
        
        mocker.patch('litellm.completion', return_value=mock_response)
        result = await self.client.generate_flashcards_from_text("Python is a programming language.")
        
        assert len(result) == 1
        assert result[0]["question"] == "What is Python?"
        assert result[0]["answer"] == "A programming language"
        assert result[0]["card_type"] == "qa"
    
    def test_generate_flashcards_from_text_sync(self, mocker):
        """Test synchronous wrapper for flashcard generation."""
        mock_response = mocker.MagicMock()
        mock_response.choices = [mocker.MagicMock()]
        mock_response.choices[0].message.content = '''[
            {
                "question": "What is Python?",
                "answer": "A programming language",
                "card_type": "qa"
            }
        ]'''
        
        mocker.patch('litellm.completion', return_value=mock_response)
        result = self.client.generate_flashcards_from_text_sync("Python is a programming language.")
        
        assert len(result) == 1
        assert result[0]["question"] == "What is Python?"
        assert result[0]["answer"] == "A programming language"
        assert result[0]["card_type"] == "qa"


class TestFlashcardData:
    """Test cases for FlashcardData dataclass."""
    
    def test_flashcard_data_creation(self):
        """Test FlashcardData creation."""
        flashcard = FlashcardData(
            question="What is Python?",
            answer="A programming language",
            card_type="qa"
        )
        
        assert flashcard.question == "What is Python?"
        assert flashcard.answer == "A programming language"
        assert flashcard.card_type == "qa"