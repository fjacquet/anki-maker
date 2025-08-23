"""
LLM Client for configurable model integration using litellm.

This module provides the LLMClient class for generating flashcards from text content
using configurable LLM models through the litellm interface. Supports multiple providers
including Gemini, OpenAI, and others based on environment configuration.
"""

import asyncio
import json
import re
from dataclasses import dataclass

from loguru import logger

from ..config import ConfigurationError, LanguageConfig, LanguageInfo, LanguageValidationError, ModelConfig
from .prompt_templates import PromptTemplates

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
    Client for interacting with configurable LLM models to generate flashcards from text content.

    This class handles text chunking, prompt engineering, API communication with retry logic,
    and parsing of LLM responses into structured flashcard data. Supports multiple LLM providers
    through environment-based configuration.
    """

    def __init__(self, model: str | None = None, max_tokens: int = 4000, language: str = "english"):
        """
        Initialize the LLM client with configurable model selection and language support.

        Args:
            model: The LLM model to use. If None, uses ModelConfig to get from environment.
            max_tokens: Maximum tokens per request chunk (default: 4000)
            language: Target language for flashcard generation (default: "english")

        Raises:
            ConfigurationError: If model is invalid or API key is missing.
            LanguageValidationError: If language is not supported.
        """
        # Use ModelConfig to validate and get the model
        if model is None:
            self.model = ModelConfig.validate_and_get_model()
        else:
            # Validate provided model
            if not ModelConfig.validate_model_config(model):
                if model not in ModelConfig.SUPPORTED_MODELS:
                    supported = ", ".join(ModelConfig.get_supported_models())
                    raise ConfigurationError(f"Unsupported model '{model}'. Supported models: {supported}")
                else:
                    required_key = ModelConfig.get_required_api_key(model)
                    raise ConfigurationError(
                        f"Missing API key for model '{model}'. Please set the {required_key} environment variable."
                    )
            self.model = model

        # Validate and normalize language using LanguageConfig
        try:
            self.language = LanguageConfig.normalize_language(language)
        except LanguageValidationError as e:
            logger.error(f"Language validation failed: {e}")
            raise

        # Get language information for logging
        self.language_info = LanguageConfig.get_language_info(self.language)

        self.max_tokens = max_tokens
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff

        # Configure litellm
        litellm.set_verbose = False

        logger.info(
            f"Initialized LLMClient with model: {self.model}, "
            f"language: {self.language_info.name} ({self.language_info.code})"
        )

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

    def get_prompt_template(self, language: str, content_type: str = "general") -> str:
        """
        Get language-specific prompt template for flashcard generation.

        Args:
            language: Target language for flashcards
            content_type: Type of content ("academic", "technical", "general")

        Returns:
            Language-specific prompt template string

        Raises:
            ValueError: If language or content_type is not supported
        """
        return PromptTemplates.get_template(language, content_type)

    def _create_flashcard_prompt(self, text: str, language: str | None = None, content_type: str = "general") -> str:
        """
        Create a carefully crafted prompt for flashcard generation using language-specific templates.

        Args:
            text: The text content to generate flashcards from
            language: Target language for flashcards (uses instance language if None)
            content_type: Type of content ("academic", "technical", "general")

        Returns:
            The formatted prompt string

        Raises:
            ValueError: If language or content_type is not supported
        """
        # Use instance language if not specified
        if language is None:
            language = self.language

        # Validate parameters
        if not PromptTemplates.validate_template_parameters(language, content_type):
            supported_langs = ", ".join(PromptTemplates.get_supported_languages())
            supported_types = ", ".join(PromptTemplates.get_supported_content_types())
            raise ValueError(
                f"Invalid parameters. Supported languages: {supported_langs}. "
                f"Supported content types: {supported_types}"
            )

        # Get template and format with text
        template = self.get_prompt_template(language, content_type)
        return template.replace("{text}", text)

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

        raise Exception(f"Failed to get response from LLM after {self.max_retries} attempts: {last_exception}")

    def _parse_flashcard_response(self, response_text: str) -> list[FlashcardData]:
        """
        Parse LLM response into structured flashcard data with robust error handling.

        Args:
            response_text: Raw response from the LLM

        Returns:
            List of FlashcardData objects
        """
        flashcards = []

        try:
            # Clean up the response text
            cleaned_response = self._clean_json_response(response_text)

            # Try to extract JSON from the response
            json_match = re.search(r"\[.*\]", cleaned_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = cleaned_response

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
            logger.debug(f"Raw response (first 500 chars): {response_text[:500]}")

            # Try to fix common JSON issues and retry
            fixed_json = self._attempt_json_fix(response_text)
            if fixed_json:
                try:
                    data = json.loads(fixed_json)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and all(
                                key in item for key in ["question", "answer", "card_type"]
                            ):
                                question = item["question"].strip()
                                answer = item["answer"].strip()
                                card_type = item["card_type"] if item["card_type"] in ["qa", "cloze"] else "qa"
                                if question and answer:
                                    flashcards.append(
                                        FlashcardData(question=question, answer=answer, card_type=card_type)
                                    )
                        logger.info(f"JSON fix successful, parsed {len(flashcards)} flashcards")
                        return flashcards
                except Exception:  # nosec B110
                    # JSON fix attempt failed, continue to fallback parsing
                    pass

            # Fallback: try to extract question-answer pairs manually
            flashcards = self._fallback_parse(response_text)

        except Exception as e:
            logger.error(f"Unexpected error parsing flashcard response: {e}")
            flashcards = self._fallback_parse(response_text)

        return flashcards

    def _clean_json_response(self, response_text: str) -> str:
        """
        Clean up common issues in JSON responses from LLMs.

        Args:
            response_text: Raw response text

        Returns:
            Cleaned response text
        """
        # Remove any text before the first [
        start_idx = response_text.find("[")
        if start_idx > 0:
            response_text = response_text[start_idx:]

        # Remove any text after the last ]
        end_idx = response_text.rfind("]")
        if end_idx != -1 and end_idx < len(response_text) - 1:
            response_text = response_text[: end_idx + 1]

        # Remove markdown code block markers
        response_text = re.sub(r"```json\s*", "", response_text)
        response_text = re.sub(r"```\s*$", "", response_text)

        return response_text.strip()

    def _attempt_json_fix(self, response_text: str) -> str | None:
        """
        Attempt to fix common JSON formatting issues.

        Args:
            response_text: Raw response text

        Returns:
            Fixed JSON string or None if unfixable
        """
        try:
            # Clean the response first
            cleaned = self._clean_json_response(response_text)

            # Try to fix trailing commas
            fixed = re.sub(r",\s*}", "}", cleaned)
            fixed = re.sub(r",\s*]", "]", fixed)

            # Try to fix missing commas between objects
            fixed = re.sub(r"}\s*{", "},{", fixed)

            # Try to fix unescaped quotes in strings
            # This is a simple approach - more sophisticated parsing might be needed
            lines = fixed.split("\n")
            for _, line in enumerate(lines):
                if '"question":' in line or '"answer":' in line:
                    # Find the value part and escape internal quotes
                    if ":" in line:
                        key_part, value_part = line.split(":", 1)
                        # Simple quote escaping - this could be improved
                        if value_part.count('"') > 2:  # More than opening and closing quotes
                            # This is a basic fix - might need more sophisticated handling
                            pass

            return fixed
        except Exception:
            return None

    def _fallback_parse(self, response_text: str) -> list[FlashcardData]:
        """
        Fallback parser for when JSON parsing fails.

        Args:
            response_text: Raw response text

        Returns:
            List of FlashcardData objects
        """
        flashcards = []

        # Try to extract individual JSON objects even if the array is malformed
        json_object_pattern = (
            r'\{\s*"question"\s*:\s*"([^"]+)"\s*,\s*"answer"\s*:\s*"([^"]+)"\s*,\s*"card_type"\s*:\s*"([^"]+)"\s*\}'
        )
        matches = re.findall(json_object_pattern, response_text, re.DOTALL | re.IGNORECASE)

        for question, answer, card_type in matches:
            question = question.strip()
            answer = answer.strip()
            card_type = card_type.strip() if card_type in ["qa", "cloze"] else "qa"
            if question and answer:
                flashcards.append(FlashcardData(question=question, answer=answer, card_type=card_type))

        if flashcards:
            logger.info(f"Fallback JSON object parser extracted {len(flashcards)} flashcards")
            return flashcards

        # Try to find question-answer patterns
        qa_patterns = [
            r"Q:\s*(.+?)\s*A:\s*(.+?)(?=Q:|$)",
            r"Question:\s*(.+?)\s*Answer:\s*(.+?)(?=Question:|$)",
            r"\d+\.\s*(.+?)\s*-\s*(.+?)(?=\d+\.|$)",
            r'"question":\s*"([^"]+)"\s*,\s*"answer":\s*"([^"]+)"',
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
            logger.info(f"Fallback pattern parser extracted {len(flashcards)} flashcards")
        else:
            logger.warning("Fallback parser could not extract any flashcards")

        return flashcards

    def _validate_response_language(
        self, flashcards: list[FlashcardData], expected_language: str
    ) -> tuple[bool, dict[str, any]]:
        """
        Validate that generated flashcards are in the expected language with detailed metrics.

        Args:
            flashcards: List of generated flashcards
            expected_language: Expected language code or name

        Returns:
            Tuple of (is_valid, validation_metrics) where validation_metrics contains:
            - success_rate: Float between 0-1 indicating pattern match rate
            - matches_found: Number of pattern matches found
            - total_checks: Total number of pattern checks performed
            - sample_size: Number of flashcards checked
            - language_info: LanguageInfo object for the expected language
            - validation_method: String describing validation method used
        """
        validation_metrics = {
            "success_rate": 0.0,
            "matches_found": 0,
            "total_checks": 0,
            "sample_size": 0,
            "language_info": None,
            "validation_method": "none",
            "patterns_used": [],
            "flashcards_checked": [],
        }

        if not flashcards:
            validation_metrics["validation_method"] = "empty_list"
            logger.debug("Language validation skipped: empty flashcard list")
            return True, validation_metrics  # Empty list is valid

        # Normalize the expected language using LanguageConfig
        try:
            normalized_language = LanguageConfig.normalize_language(expected_language)
            language_info = LanguageConfig.get_language_info(normalized_language)
            validation_metrics["language_info"] = language_info
        except LanguageValidationError:
            validation_metrics["validation_method"] = "unsupported_language"
            logger.warning(f"Cannot validate unknown language: {expected_language}")
            return True, validation_metrics  # Skip validation for unsupported languages

        # Enhanced language validation patterns with more comprehensive coverage
        language_patterns = {
            "english": [
                # Common articles, prepositions, and conjunctions
                r"\b(the|and|or|is|are|was|were|have|has|had|will|would|can|could|should|may|might)\b",
                # Question words
                r"\b(what|when|where|why|how|who|which)\b",
                # Demonstratives and pronouns
                r"\b(this|that|these|those|it|they|them|their|there)\b",
                # Common verbs
                r"\b(do|does|did|get|got|make|made|take|took|come|came|go|went)\b",
                # English-specific patterns
                r"\b(of|to|in|for|with|by|from|up|about|into|through|during)\b",
            ],
            "french": [
                # Articles and basic words
                r"\b(le|la|les|un|une|des|et|ou|est|sont|était|étaient|avoir|être)\b",
                # Question words
                r"\b(quel|quelle|quels|quelles|qui|que|quoi|où|quand|comment|pourquoi)\b",
                # Demonstratives and pronouns
                r"\b(ce|cette|ces|ceux|celles|il|elle|ils|elles|leur|leurs)\b",
                # Prepositions and conjunctions
                r"\b(dans|sur|avec|pour|par|de|du|des|à|au|aux|mais|donc|car|si)\b",
                # French-specific patterns
                r"\b(très|plus|moins|bien|mal|tout|tous|toute|toutes|même|déjà)\b",
            ],
            "italian": [
                # Articles and basic words
                r"\b(il|la|lo|gli|le|un|una|e|o|è|sono|era|erano|avere|essere)\b",
                # Question words
                r"\b(che|chi|cosa|dove|quando|come|perché|quale|quali|quanto|quanta)\b",
                # Demonstratives and pronouns
                r"\b(questo|questa|questi|queste|quello|quella|quelli|quelle|loro)\b",
                # Prepositions and conjunctions
                r"\b(in|su|con|per|da|di|del|della|dei|delle|ma|però|anche|già)\b",
                # Italian-specific patterns
                r"\b(molto|più|meno|bene|male|tutto|tutti|tutta|tutte|stesso|stessa)\b",
            ],
            "german": [
                # Articles and basic words
                r"\b(der|die|das|ein|eine|und|oder|ist|sind|war|waren|haben|sein)\b",
                # Question words
                r"\b(was|wer|wo|wann|wie|warum|welche|welcher|welches|wieviel)\b",
                # Demonstratives and pronouns
                r"\b(dieser|diese|dieses|jener|jene|jenes|sie|ihr|ihre|ihren)\b",
                # Prepositions and conjunctions
                r"\b(in|auf|mit|für|von|zu|bei|nach|über|unter|aber|doch|auch|schon)\b",
                # German-specific patterns
                r"\b(sehr|mehr|weniger|gut|schlecht|alle|alles|ganz|noch|nicht)\b",
            ],
        }

        # Use the prompt key for pattern matching
        patterns = language_patterns.get(language_info.prompt_key, [])
        validation_metrics["patterns_used"] = patterns

        if not patterns:
            validation_metrics["validation_method"] = "no_patterns"
            logger.warning(f"No validation patterns available for language: {language_info.name}")
            return True, validation_metrics  # Skip validation for languages without patterns

        # Check a sample of flashcards for language patterns
        sample_size = min(5, len(flashcards))
        sample_flashcards = flashcards[:sample_size]
        validation_metrics["sample_size"] = sample_size
        validation_metrics["validation_method"] = "pattern_matching"

        matches = 0
        total_checks = 0
        checked_flashcards = []

        for i, flashcard in enumerate(sample_flashcards):
            text_to_check = f"{flashcard.question} {flashcard.answer}".lower()
            flashcard_matches = 0

            for pattern in patterns:
                if re.search(pattern, text_to_check, re.IGNORECASE):
                    matches += 1
                    flashcard_matches += 1
                total_checks += 1

            checked_flashcards.append(
                {
                    "index": i,
                    "question": flashcard.question[:50] + "..." if len(flashcard.question) > 50 else flashcard.question,
                    "answer": flashcard.answer[:50] + "..." if len(flashcard.answer) > 50 else flashcard.answer,
                    "matches": flashcard_matches,
                    "total_patterns": len(patterns),
                }
            )

        validation_metrics["matches_found"] = matches
        validation_metrics["total_checks"] = total_checks
        validation_metrics["flashcards_checked"] = checked_flashcards

        # Consider validation successful if we find language patterns in at least 30% of checks
        if total_checks > 0:
            success_rate = matches / total_checks
            validation_metrics["success_rate"] = success_rate
            is_valid = success_rate >= 0.3

            if not is_valid:
                logger.warning(
                    f"Language validation failed for {language_info.name}. "
                    f"Success rate: {success_rate:.2%} (expected >= 30%). "
                    f"Found {matches}/{total_checks} pattern matches across {sample_size} flashcards."
                )
                # Log detailed breakdown for debugging
                logger.debug(f"Validation details: {validation_metrics}")
            else:
                logger.debug(
                    f"Language validation passed for {language_info.name}. "
                    f"Success rate: {success_rate:.2%} ({matches}/{total_checks} matches)"
                )

            return is_valid, validation_metrics

        # If no patterns to check, assume valid
        validation_metrics["validation_method"] = "no_checks_performed"
        return True, validation_metrics

    async def _generate_flashcards_with_language_validation(
        self, text: str, language: str, content_type: str = "general", max_validation_retries: int = 2
    ) -> tuple[list[FlashcardData], dict[str, any]]:
        """
        Generate flashcards with language validation and retry mechanism.

        Args:
            text: The input text to generate flashcards from
            language: Target language for flashcards
            content_type: Type of content ("academic", "technical", "general")
            max_validation_retries: Maximum number of retries for language validation failures

        Returns:
            Tuple of (flashcards, validation_summary) where validation_summary contains:
            - total_attempts: Number of generation attempts made
            - validation_results: List of validation results for each attempt
            - final_validation_passed: Whether final validation passed
            - fallback_used: Whether fallback behavior was triggered
        """
        validation_summary = {
            "total_attempts": 0,
            "validation_results": [],
            "final_validation_passed": False,
            "fallback_used": False,
            "language_requested": language,
            "content_type": content_type,
        }

        last_flashcards = []
        last_exception = None

        for attempt in range(max_validation_retries + 1):  # +1 for initial attempt
            validation_summary["total_attempts"] = attempt + 1

            try:
                logger.debug(f"Language validation attempt {attempt + 1}/{max_validation_retries + 1} for {language}")

                # Create prompt for this attempt
                prompt = self._create_flashcard_prompt(text, language=language, content_type=content_type)

                # Make API call with retry logic
                response = await self._make_api_call_with_retry(prompt)

                # Parse response into flashcard data
                flashcards = self._parse_flashcard_response(response)

                if not flashcards:
                    logger.warning(f"No flashcards generated on attempt {attempt + 1}")
                    continue

                # Validate language
                is_valid, validation_metrics = self._validate_response_language(flashcards, language)
                validation_result = {
                    "attempt": attempt + 1,
                    "flashcards_generated": len(flashcards),
                    "validation_passed": is_valid,
                    "validation_metrics": validation_metrics,
                }
                validation_summary["validation_results"].append(validation_result)

                if is_valid:
                    validation_summary["final_validation_passed"] = True
                    logger.info(
                        f"Language validation passed on attempt {attempt + 1}. "
                        f"Generated {len(flashcards)} flashcards in {validation_metrics['language_info'].name}"
                    )
                    return flashcards, validation_summary
                else:
                    logger.warning(
                        f"Language validation failed on attempt {attempt + 1}. "
                        f"Expected {language}, success rate: {validation_metrics['success_rate']:.2%}"
                    )
                    last_flashcards = flashcards

                    # If this is not the last attempt, try again
                    if attempt < max_validation_retries:
                        logger.info("Retrying flashcard generation with adjusted prompt...")
                        # Add small delay before retry
                        await asyncio.sleep(1.0)

            except Exception as e:
                last_exception = e
                logger.error(f"Error during flashcard generation attempt {attempt + 1}: {e}")
                validation_result = {
                    "attempt": attempt + 1,
                    "flashcards_generated": 0,
                    "validation_passed": False,
                    "error": str(e),
                }
                validation_summary["validation_results"].append(validation_result)

                if attempt < max_validation_retries:
                    await asyncio.sleep(1.0)

        # All validation attempts failed - implement fallback behavior
        logger.warning(
            f"All {max_validation_retries + 1} language validation attempts failed for {language}. "
            "Implementing fallback behavior."
        )

        validation_summary["fallback_used"] = True

        # Fallback strategy 1: Return the best flashcards we got (if any)
        if last_flashcards:
            logger.info(
                f"Fallback: Using {len(last_flashcards)} flashcards from last attempt despite validation failure"
            )
            return last_flashcards, validation_summary

        # Fallback strategy 2: Try with English if original language wasn't English
        if language.lower() not in ["english", "en"]:
            logger.info("Fallback: Attempting generation in English as last resort")
            try:
                prompt = self._create_flashcard_prompt(text, language="english", content_type=content_type)
                response = await self._make_api_call_with_retry(prompt)
                fallback_flashcards = self._parse_flashcard_response(response)

                if fallback_flashcards:
                    logger.warning(
                        f"Fallback successful: Generated {len(fallback_flashcards)} flashcards in English "
                        f"instead of requested {language}"
                    )
                    validation_summary["fallback_language"] = "english"
                    return fallback_flashcards, validation_summary

            except Exception as e:
                logger.error(f"Fallback to English also failed: {e}")

        # Final fallback: Return empty list
        logger.error(
            f"All fallback strategies failed. Unable to generate flashcards for text in {language}. "
            f"Last error: {last_exception}"
        )
        return [], validation_summary

    async def generate_flashcards_from_text(
        self, text: str, language: str | None = None, content_type: str = "general"
    ) -> list[dict[str, str]]:
        """
        Generate flashcards from text content using configurable LLM with multi-language support.

        Args:
            text: The input text to generate flashcards from
            language: Target language for flashcards (uses Settings configuration if None)
            content_type: Type of content ("academic", "technical", "general", default: "general")

        Returns:
            List of dictionaries containing flashcard data
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for flashcard generation")
            return []

        # Use Settings configuration if language not specified, fallback to instance language
        if language is None:
            try:
                from ..config import settings

                language = settings.cardlang
                logger.debug(f"Using language from Settings configuration: {language}")
            except Exception as e:
                logger.warning(f"Failed to get language from Settings, using instance language: {e}")
                language = self.language

        # Get language info for better logging
        try:
            lang_info = LanguageConfig.get_language_info(language)
            logger.info(
                f"Generating {lang_info.name} ({lang_info.code}) flashcards from text "
                f"({len(text)} characters) - Content type: {content_type}"
            )
        except LanguageValidationError:
            logger.info(
                f"Generating {language} flashcards from text ({len(text)} characters) - Content type: {content_type}"
            )

        # Chunk the text if it's too long
        text_chunks = self.chunk_text_for_processing(text)
        all_flashcards = []

        # Track overall validation statistics
        overall_validation_stats = {
            "total_chunks": len(text_chunks),
            "successful_chunks": 0,
            "failed_chunks": 0,
            "validation_failures": 0,
            "fallback_used": 0,
            "chunk_results": [],
        }

        for i, chunk in enumerate(text_chunks):
            try:
                lang_info = LanguageConfig.get_language_info(language)
                logger.info(f"Processing chunk {i + 1}/{len(text_chunks)} for {lang_info.name} flashcards")
            except LanguageValidationError:
                logger.info(f"Processing chunk {i + 1}/{len(text_chunks)} for {language} flashcards")

            try:
                # Use enhanced language validation with retry mechanism
                chunk_flashcards, validation_summary = await self._generate_flashcards_with_language_validation(
                    chunk, language=language, content_type=content_type, max_validation_retries=2
                )

                # Track chunk results
                chunk_result = {
                    "chunk_index": i + 1,
                    "flashcards_generated": len(chunk_flashcards),
                    "validation_summary": validation_summary,
                }
                overall_validation_stats["chunk_results"].append(chunk_result)

                if chunk_flashcards:
                    overall_validation_stats["successful_chunks"] += 1

                    # Track validation statistics
                    if not validation_summary["final_validation_passed"]:
                        overall_validation_stats["validation_failures"] += 1

                    if validation_summary["fallback_used"]:
                        overall_validation_stats["fallback_used"] += 1

                    # Convert to dictionary format
                    for flashcard in chunk_flashcards:
                        all_flashcards.append(
                            {
                                "question": flashcard.question,
                                "answer": flashcard.answer,
                                "card_type": flashcard.card_type,
                            }
                        )

                    try:
                        lang_info = LanguageConfig.get_language_info(language)
                        logger.info(
                            f"Generated {len(chunk_flashcards)} {lang_info.name} flashcards from chunk {i + 1} "
                            f"(validation: {'passed' if validation_summary['final_validation_passed'] else 'failed'}, "
                            f"attempts: {validation_summary['total_attempts']})"
                        )
                    except LanguageValidationError:
                        logger.info(
                            f"Generated {len(chunk_flashcards)} {language} flashcards from chunk {i + 1} "
                            f"(validation: {'passed' if validation_summary['final_validation_passed'] else 'failed'})"
                        )
                else:
                    overall_validation_stats["failed_chunks"] += 1
                    logger.warning(f"No flashcards generated for chunk {i + 1}")

                # Add small delay between chunks to be respectful to the API
                if i < len(text_chunks) - 1:
                    await asyncio.sleep(0.5)

            except Exception as e:
                overall_validation_stats["failed_chunks"] += 1
                logger.error(f"Failed to process chunk {i + 1}: {e}")
                continue

        # Log comprehensive validation summary
        self._log_validation_summary(language, overall_validation_stats)

        try:
            lang_info = LanguageConfig.get_language_info(language)
            logger.info(f"Total {lang_info.name} flashcards generated: {len(all_flashcards)}")
        except LanguageValidationError:
            logger.info(f"Total {language} flashcards generated: {len(all_flashcards)}")
        return all_flashcards

    def _log_validation_summary(self, language: str, validation_stats: dict[str, any]) -> None:
        """
        Log comprehensive validation summary for language validation results.

        Args:
            language: Target language that was requested
            validation_stats: Dictionary containing validation statistics
        """
        try:
            lang_info = LanguageConfig.get_language_info(language)
            language_display = f"{lang_info.name} ({lang_info.code})"
        except LanguageValidationError:
            language_display = language

        total_chunks = validation_stats["total_chunks"]
        successful_chunks = validation_stats["successful_chunks"]
        failed_chunks = validation_stats["failed_chunks"]
        validation_failures = validation_stats["validation_failures"]
        fallback_used = validation_stats["fallback_used"]

        # Calculate success rates
        success_rate = (successful_chunks / total_chunks * 100) if total_chunks > 0 else 0
        validation_failure_rate = (validation_failures / successful_chunks * 100) if successful_chunks > 0 else 0

        logger.info(
            f"Language validation summary for {language_display}:\n"
            f"  • Total chunks processed: {total_chunks}\n"
            f"  • Successful chunks: {successful_chunks}/{total_chunks} ({success_rate:.1f}%)\n"
            f"  • Failed chunks: {failed_chunks}\n"
            f"  • Language validation failures: {validation_failures} ({validation_failure_rate:.1f}%)\n"
            f"  • Fallback behavior used: {fallback_used} times"
        )

        # Log warnings for concerning patterns
        if validation_failure_rate > 50:
            logger.warning(
                f"High language validation failure rate ({validation_failure_rate:.1f}%) for {language_display}. "
                "Consider checking prompt templates or language patterns."
            )

        if fallback_used > 0:
            logger.warning(
                f"Fallback behavior was used {fallback_used} times for {language_display}. "
                "This may indicate issues with language-specific generation."
            )

        if failed_chunks > total_chunks * 0.3:  # More than 30% failed
            logger.warning(
                f"High chunk failure rate ({failed_chunks}/{total_chunks}) for {language_display}. "
                "Consider reviewing input text or model configuration."
            )

        # Log detailed chunk results in debug mode
        logger.debug(f"Detailed chunk results for {language_display}: {validation_stats['chunk_results']}")

    def generate_flashcards_from_text_sync(
        self, text: str, language: str | None = None, content_type: str = "general"
    ) -> list[dict[str, str]]:
        """
        Synchronous wrapper for generate_flashcards_from_text.

        Args:
            text: The input text to generate flashcards from
            language: Target language for flashcards (uses Settings configuration if None)
            content_type: Type of content ("academic", "technical", "general", default: "general")

        Returns:
            List of dictionaries containing flashcard data
        """
        return asyncio.run(self.generate_flashcards_from_text(text, language=language, content_type=content_type))

    def validate_model_and_api_key(self, model: str) -> bool:
        """
        Validate that a model is supported and has the required API key.

        Args:
            model: The model identifier to validate

        Returns:
            True if model is valid and API key is available, False otherwise
        """
        return ModelConfig.validate_model_config(model)

    def get_supported_models(self) -> list[str]:
        """
        Get list of supported model identifiers.

        Returns:
            List of supported model strings
        """
        return ModelConfig.get_supported_models()

    def get_current_model(self) -> str:
        """
        Get the currently configured model.

        Returns:
            The current model identifier
        """
        return self.model

    def get_current_language(self) -> str:
        """
        Get the currently configured language.

        Returns:
            The current language identifier
        """
        return self.language

    def get_language_info(self) -> LanguageInfo:
        """
        Get detailed information about the currently configured language.

        Returns:
            LanguageInfo object with code, name, and prompt_key
        """
        return self.language_info

    def set_language(self, language: str) -> None:
        """
        Update the language configuration for the LLM client.

        Args:
            language: New target language for flashcard generation

        Raises:
            LanguageValidationError: If language is not supported
        """
        try:
            self.language = LanguageConfig.normalize_language(language)
            self.language_info = LanguageConfig.get_language_info(self.language)
            logger.info(f"Updated LLMClient language to: {self.language_info.name} ({self.language_info.code})")
        except LanguageValidationError as e:
            logger.error(f"Failed to set language: {e}")
            raise
