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

from ..config import ConfigurationError, ModelConfig

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

    def __init__(self, model: str | None = None, max_tokens: int = 4000):
        """
        Initialize the LLM client with configurable model selection.

        Args:
            model: The LLM model to use. If None, uses ModelConfig to get from environment.
            max_tokens: Maximum tokens per request chunk (default: 4000)

        Raises:
            ConfigurationError: If model is invalid or API key is missing.
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

        self.max_tokens = max_tokens
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff

        # Configure litellm
        litellm.set_verbose = False

        logger.info(f"Initialized LLMClient with model: {self.model}")

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

    def get_french_prompt_template(self, content_type: str = "general") -> str:
        """
        Get French-specific prompt template for flashcard generation.

        Args:
            content_type: Type of content ("academic", "technical", "general")

        Returns:
            French prompt template string
        """
        base_instructions = """Vous êtes un expert en création de cartes mémoire (flashcards) pour l'apprentissage efficace et la rétention à long terme.

RÈGLES CRITIQUES DE FORMATAGE JSON:
- Votre réponse doit être UNIQUEMENT un tableau JSON valide, rien d'autre
- Aucun texte explicatif avant ou après le JSON
- Utilisez des guillemets doubles pour toutes les chaînes
- Échappez les guillemets à l'intérieur des chaînes avec des barres obliques inverses
- Assurez-vous que tous les objets JSON sont correctement fermés avec des virgules entre eux
- Le dernier objet du tableau ne doit PAS avoir de virgule finale

INSTRUCTIONS IMPORTANTES:
1. Analysez le texte fourni et identifiez les concepts, faits et relations les plus importants
2. Créez un mélange de cartes question-réponse et de cartes à trous (cloze deletion)
3. Concentrez-vous sur les informations clés qui seraient précieuses pour la rétention à long terme
4. Formulez des questions claires, spécifiques et sans ambiguïté EN FRANÇAIS
5. Assurez-vous que les réponses sont concises mais complètes EN FRANÇAIS
6. Créez des suppressions à trous pour les termes importants, dates et concepts

EXIGENCES LINGUISTIQUES CRITIQUES:
- TOUTES les questions DOIVENT être en français
- TOUTES les réponses DOIVENT être en français
- Utilisez une grammaire française correcte et un vocabulaire approprié
- Respectez les accords de genre et de nombre
- Adaptez le registre de langue au contenu"""

        content_specific = {
            "academic": """
- Utilisez un vocabulaire académique précis
- Privilégiez la terminologie scientifique française
- Créez des questions qui testent la compréhension conceptuelle
- Incluez des définitions et des explications détaillées""",
            "technical": """
- Utilisez la terminologie technique française appropriée
- Créez des questions sur les processus et procédures
- Incluez des questions sur les causes et effets
- Privilégiez la précision technique""",
            "general": """
- Utilisez un français accessible et clair
- Créez des questions variées sur les faits principaux
- Incluez des questions de compréhension générale
- Adaptez le niveau de langue au contenu"""
        }

        specific_instructions = content_specific.get(content_type, content_specific["general"])

        return f"""{base_instructions}

{specific_instructions}

EXIGENCES DES CARTES MÉMOIRE:
- Chaque carte mémoire doit avoir exactement ces champs: "question", "answer", "card_type"
- card_type doit être soit "qa" (question-réponse) soit "cloze" (suppression à trous)
- Pour les cartes cloze, utilisez le format {{{{c1::texte}}}} dans le champ question
- Visez 10-50 cartes mémoire selon la richesse du contenu
- Privilégiez la qualité à la quantité

EXEMPLE DE SORTIE JSON VALIDE:
[
  {{
    "question": "Quelle est la capitale de la France ?",
    "answer": "Paris",
    "card_type": "qa"
  }},
  {{
    "question": "La capitale de la France est {{{{c1::Paris}}}}",
    "answer": "Paris",
    "card_type": "cloze"
  }}
]

TEXTE À TRAITER:
{{text}}

TABLEAU JSON:"""

    def _create_flashcard_prompt(self, text: str, language: str = "french", content_type: str = "general") -> str:
        """
        Create a carefully crafted prompt for flashcard generation.

        Args:
            text: The text content to generate flashcards from
            language: Target language for flashcards ("french" or "english")
            content_type: Type of content ("academic", "technical", "general")

        Returns:
            The formatted prompt string
        """
        if language == "french":
            template = self.get_french_prompt_template(content_type)
            return template.format(text=text)
        
        # Default English prompt (existing implementation)
        prompt = f"""You are an expert educator creating high-quality Anki flashcards for effective learning and retention.

CRITICAL JSON FORMATTING RULES:
- Your response must be ONLY a valid JSON array, nothing else
- No explanatory text before or after the JSON
- Use double quotes for all strings
- Escape any quotes inside strings with backslashes
- Ensure all JSON objects are properly closed with commas between them
- The last object in the array should NOT have a trailing comma

INSTRUCTIONS:
1. Analyze the following text and identify the most important concepts, facts, and relationships
2. Create a mix of question-answer pairs and cloze deletion cards
3. Focus on key information that would be valuable for long-term retention
4. Make questions clear, specific, and unambiguous
5. Ensure answers are concise but complete
6. Create cloze deletions for important terms, dates, and concepts

FLASHCARD REQUIREMENTS:
- Each flashcard must have exactly these fields: "question", "answer", "card_type"
- card_type must be either "qa" (question-answer) or "cloze" (cloze deletion)
- For cloze cards, use {{{{c1::text}}}} format in the question field
- Aim for 10-50 flashcards depending on content richness
- Prioritize quality over quantity

EXAMPLE VALID JSON OUTPUT:
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

JSON ARRAY:"""

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
                            if isinstance(item, dict) and all(key in item for key in ["question", "answer", "card_type"]):
                                question = item["question"].strip()
                                answer = item["answer"].strip()
                                card_type = item["card_type"] if item["card_type"] in ["qa", "cloze"] else "qa"
                                if question and answer:
                                    flashcards.append(FlashcardData(question=question, answer=answer, card_type=card_type))
                        logger.info(f"JSON fix successful, parsed {len(flashcards)} flashcards")
                        return flashcards
                except:
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
        start_idx = response_text.find('[')
        if start_idx > 0:
            response_text = response_text[start_idx:]
        
        # Remove any text after the last ]
        end_idx = response_text.rfind(']')
        if end_idx != -1 and end_idx < len(response_text) - 1:
            response_text = response_text[:end_idx + 1]
        
        # Remove markdown code block markers
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*$', '', response_text)
        
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
            fixed = re.sub(r',\s*}', '}', cleaned)
            fixed = re.sub(r',\s*]', ']', fixed)
            
            # Try to fix missing commas between objects
            fixed = re.sub(r'}\s*{', '},{', fixed)
            
            # Try to fix unescaped quotes in strings
            # This is a simple approach - more sophisticated parsing might be needed
            lines = fixed.split('\n')
            for i, line in enumerate(lines):
                if '"question":' in line or '"answer":' in line:
                    # Find the value part and escape internal quotes
                    if ':' in line:
                        key_part, value_part = line.split(':', 1)
                        # Simple quote escaping - this could be improved
                        if value_part.count('"') > 2:  # More than opening and closing quotes
                            # This is a basic fix - might need more sophisticated handling
                            pass
            
            return fixed
        except:
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
        json_object_pattern = r'\{\s*"question"\s*:\s*"([^"]+)"\s*,\s*"answer"\s*:\s*"([^"]+)"\s*,\s*"card_type"\s*:\s*"([^"]+)"\s*\}'
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

    async def generate_flashcards_from_text(self, text: str, language: str = "french", content_type: str = "general") -> list[dict[str, str]]:
        """
        Generate flashcards from text content using configurable LLM with French language support.

        Args:
            text: The input text to generate flashcards from
            language: Target language for flashcards ("french" or "english", default: "french")
            content_type: Type of content ("academic", "technical", "general", default: "general")

        Returns:
            List of dictionaries containing flashcard data
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for flashcard generation")
            return []

        logger.info(f"Generating {language} flashcards from text ({len(text)} characters) - Content type: {content_type}")

        # Chunk the text if it's too long
        text_chunks = self.chunk_text_for_processing(text)
        all_flashcards = []

        for i, chunk in enumerate(text_chunks):
            logger.info(f"Processing chunk {i + 1}/{len(text_chunks)} for {language} flashcards")

            try:
                # Create prompt for this chunk with language and content type
                prompt = self._create_flashcard_prompt(chunk, language=language, content_type=content_type)

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

                logger.info(f"Generated {len(chunk_flashcards)} {language} flashcards from chunk {i + 1}")

                # Add small delay between chunks to be respectful to the API
                if i < len(text_chunks) - 1:
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Failed to process chunk {i + 1}: {e}")
                continue

        logger.info(f"Total {language} flashcards generated: {len(all_flashcards)}")
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
