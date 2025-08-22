"""
LLM Client for Gemini integration using litellm.

This module provides the LLMClient class for generating flashcards from text content
using Google's Gemini Pro model through the litellm interface.
"""

import asyncio
import json
import re
from dataclasses import dataclass

from loguru import logger

try:
    import litellm
except ImportError:
    logger.error("litellm is required but not installed. Please install it with: pip install litellm")
    raise


@dataclass
class FlashcardData:
    """Data structure for flashcard information from LLM response."""

    question: str
    answer: str
    card_type: str  # "qa" or "cloze"


class LLMClient:
    """
    Client for interacting with Gemini LLM to generate flashcards from text content.

    This class handles text chunking, prompt engineering, API communication with retry logic,
    and parsing of LLM responses into structured flashcard data.
    """

    def __init__(self, model: str = "gemini/gemini-2.5-flash", max_tokens: int = 4000):
        """
        Initialize the LLM client.

        Args:
            model: The LLM model to use (default: gemini/gemini-pro)
            max_tokens: Maximum tokens per request chunk (default: 4000)
        """
        self.model = model
        self.max_tokens = max_tokens
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff

        # Configure litellm
        litellm.set_verbose = False

    def chunk_text_for_processing(self, text: str, max_tokens: int | None = None) -> list[str]:
        """
        Split large text into manageable chunks for LLM processing.

        Args:
            text: The input text to chunk
            max_tokens: Maximum tokens per chunk (uses instance default if None)

        Returns:
            List of text chunks
        """
        if max_tokens is None:
            max_tokens = self.max_tokens

        # Rough estimation: 1 token ≈ 4 characters for English text
        max_chars = max_tokens * 4

        if len(text) <= max_chars:
            return [text]

        chunks = []
        current_chunk = ""

        # Split by paragraphs first to maintain context
        paragraphs = text.split("\n\n")

        for paragraph in paragraphs:
            # If adding this paragraph would exceed the limit
            if len(current_chunk) + len(paragraph) + 2 > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # If single paragraph is too long, split by sentences
                if len(paragraph) > max_chars:
                    sentences = re.split(r"[.!?]+", paragraph)
                    temp_chunk = ""

                    for sentence in sentences:
                        if len(temp_chunk) + len(sentence) + 1 > max_chars:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                                temp_chunk = ""
                        temp_chunk += sentence + ". "

                    if temp_chunk.strip():
                        current_chunk = temp_chunk.strip()
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        logger.info(f"Split text into {len(chunks)} chunks for processing")
        return chunks

    def _create_flashcard_prompt(self, text: str) -> str:
        """
        Create a carefully crafted prompt for flashcard generation.

        Args:
            text: The text content to generate flashcards from

        Returns:
            The formatted prompt string
        """
        prompt = f"""You are an expert educator creating high-quality Anki flashcards for effective \
learning and retention.

INSTRUCTIONS:
1. Analyze the following text and identify the most important concepts, facts, and relationships
2. Create a mix of question-answer pairs and cloze deletion cards
3. Focus on key information that would be valuable for long-term retention
4. Make questions clear, specific, and unambiguous
5. Ensure answers are concise but complete
6. Create cloze deletions for important terms, dates, and concepts

FORMATTING REQUIREMENTS:
- Return ONLY a valid JSON array
- Each flashcard must have exactly these fields: "question", "answer", "card_type"
- card_type must be either "qa" (question-answer) or "cloze" (cloze deletion)
- For cloze cards, use {{{{c1::text}}}} format in the question field
- Aim for 50-150 flashcards depending on content richness
- Prioritize quality over quantity

EXAMPLE OUTPUT:
[
  {{
    "question": "What is the capital of France?",
    "answer": "Paris",
    "card_type": "qa"
  }},
  {{
    "question": "The capital of France is {{{{c1::Paris}}}}",
    "answer": "Paris",
    "card_type": "cloze"
  }}
]

TEXT TO PROCESS:
{text}

Generate flashcards as a JSON array:"""

        return prompt

    async def _make_api_call_with_retry(self, prompt: str) -> str:
        """
        Make API call with exponential backoff retry logic.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            The LLM response text

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Making API call attempt {attempt + 1}/{self.max_retries}")

                response = await asyncio.to_thread(
                    litellm.completion,
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,  # Lower temperature for more consistent output
                    max_tokens=20000,  # Enough for multiple flashcards
                )

                if response and response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    if content and isinstance(content, str):
                        logger.debug("API call successful")
                        result: str = content.strip()
                        return result

                raise Exception("Empty response from LLM")

            except Exception as e:
                last_exception = e
                logger.warning(f"API call attempt {attempt + 1} failed: {str(e)}")

                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2**attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} API call attempts failed")

        raise Exception(
            f"Failed to get response from LLM after {self.max_retries} attempts: {last_exception}"
        )

    def _parse_flashcard_response(self, response_text: str) -> list[FlashcardData]:
        """
        Parse LLM response into structured flashcard data.

        Args:
            response_text: Raw response from the LLM

        Returns:
            List of FlashcardData objects
        """
        flashcards = []

        try:
            # Try to extract JSON from the response
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text

            # Parse JSON
            data = json.loads(json_str)

            if not isinstance(data, list):
                logger.warning("Response is not a JSON array, attempting to wrap it")
                data = [data] if isinstance(data, dict) else []

            for item in data:
                if not isinstance(item, dict):
                    logger.warning(f"Skipping invalid flashcard item: {item}")
                    continue

                # Validate required fields
                if not all(key in item for key in ["question", "answer", "card_type"]):
                    logger.warning(f"Skipping flashcard with missing fields: {item}")
                    continue

                # Validate card_type
                if item["card_type"] not in ["qa", "cloze"]:
                    logger.warning(f"Invalid card_type '{item['card_type']}', defaulting to 'qa'")
                    item["card_type"] = "qa"

                # Clean up the content
                question = item["question"].strip()
                answer = item["answer"].strip()
                card_type = item["card_type"]

                if question and answer:
                    flashcards.append(FlashcardData(question=question, answer=answer, card_type=card_type))
                else:
                    logger.warning(f"Skipping flashcard with empty question or answer: {item}")

            logger.info(f"Successfully parsed {len(flashcards)} flashcards from LLM response")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response_text}")

            # Fallback: try to extract question-answer pairs manually
            flashcards = self._fallback_parse(response_text)

        except Exception as e:
            logger.error(f"Unexpected error parsing flashcard response: {e}")
            flashcards = self._fallback_parse(response_text)

        return flashcards

    def _fallback_parse(self, response_text: str) -> list[FlashcardData]:
        """
        Fallback parser for when JSON parsing fails.

        Args:
            response_text: Raw response text

        Returns:
            List of FlashcardData objects
        """
        flashcards = []

        # Try to find question-answer patterns
        qa_patterns = [
            r"Q:\s*(.+?)\s*A:\s*(.+?)(?=Q:|$)",
            r"Question:\s*(.+?)\s*Answer:\s*(.+?)(?=Question:|$)",
            r"\d+\.\s*(.+?)\s*-\s*(.+?)(?=\d+\.|$)",
        ]

        for pattern in qa_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if matches:
                for question, answer in matches:
                    question = question.strip()
                    answer = answer.strip()
                    if question and answer:
                        flashcards.append(FlashcardData(question=question, answer=answer, card_type="qa"))
                break

        if flashcards:
            logger.info(f"Fallback parser extracted {len(flashcards)} flashcards")
        else:
            logger.warning("Fallback parser could not extract any flashcards")

        return flashcards

    async def generate_flashcards_from_text(self, text: str) -> list[dict[str, str]]:
        """
        Generate flashcards from text content using Gemini LLM.

        Args:
            text: The input text to generate flashcards from

        Returns:
            List of dictionaries containing flashcard data
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for flashcard generation")
            return []

        logger.info(f"Generating flashcards from text ({len(text)} characters)")

        # Chunk the text if it's too long
        text_chunks = self.chunk_text_for_processing(text)
        all_flashcards = []

        for i, chunk in enumerate(text_chunks):
            logger.info(f"Processing chunk {i + 1}/{len(text_chunks)}")

            try:
                # Create prompt for this chunk
                prompt = self._create_flashcard_prompt(chunk)

                # Make API call with retry logic
                response = await self._make_api_call_with_retry(prompt)

                # Parse response into flashcard data
                chunk_flashcards = self._parse_flashcard_response(response)

                # Convert to dictionary format
                for flashcard in chunk_flashcards:
                    all_flashcards.append(
                        {
                            "question": flashcard.question,
                            "answer": flashcard.answer,
                            "card_type": flashcard.card_type,
                        }
                    )

                logger.info(f"Generated {len(chunk_flashcards)} flashcards from chunk {i + 1}")

                # Add small delay between chunks to be respectful to the API
                if i < len(text_chunks) - 1:
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Failed to process chunk {i + 1}: {e}")
                continue

        logger.info(f"Total flashcards generated: {len(all_flashcards)}")
        return all_flashcards

    def generate_flashcards_from_text_sync(self, text: str) -> list[dict[str, str]]:
        """
        Synchronous wrapper for generate_flashcards_from_text.

        Args:
            text: The input text to generate flashcards from

        Returns:
            List of dictionaries containing flashcard data
        """
        return asyncio.run(self.generate_flashcards_from_text(text))
