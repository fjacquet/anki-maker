"""
Language-specific prompt templates for flashcard generation.

This module provides comprehensive prompt templates for generating flashcards
in different languages (English, French, Italian, German) with support for
different content types (academic, technical, general).
"""


class PromptTemplates:
    """Manages language-specific prompt templates for flashcard generation."""

    @staticmethod
    def get_template(language: str, content_type: str = "general") -> str:
        """
        Get language-specific prompt template for flashcard generation.

        Args:
            language: Target language ("english", "french", "italian", "german")
            content_type: Type of content ("academic", "technical", "general")

        Returns:
            Formatted prompt template string

        Raises:
            ValueError: If language or content_type is not supported
        """
        language = language.lower().strip()
        content_type = content_type.lower().strip()

        # Map language codes to full names
        language_map = {"en": "english", "fr": "french", "it": "italian", "de": "german"}

        if language in language_map:
            language = language_map[language]

        if language == "english":
            return PromptTemplates._get_english_template(content_type)
        elif language == "french":
            return PromptTemplates._get_french_template(content_type)
        elif language == "italian":
            return PromptTemplates._get_italian_template(content_type)
        elif language == "german":
            return PromptTemplates._get_german_template(content_type)
        else:
            raise ValueError(f"Unsupported language: {language}")

    @staticmethod
    def _get_english_template(content_type: str) -> str:
        """Get English prompt template."""
        base_instructions = """You are an expert educator creating high-quality Anki flashcards
         for effective learning and retention.

CRITICAL JSON FORMATTING RULES:
- Your response must be ONLY a valid JSON array, nothing else
- No explanatory text before or after the JSON
- Use double quotes for all strings
- Escape any quotes inside strings with backslashes
- Ensure all JSON objects are properly closed with commas between them
- The last object in the array should NOT have a trailing comma

IMPORTANT INSTRUCTIONS:
1. Analyze the provided text and identify the most important concepts, facts, and relationships
2. Create a mix of question-answer pairs and cloze deletion cards
3. Focus on key information that would be valuable for long-term retention
4. Formulate clear, specific, and unambiguous questions IN ENGLISH
5. Ensure answers are concise but complete IN ENGLISH
6. Create cloze deletions for important terms, dates, and concepts

CRITICAL LANGUAGE REQUIREMENTS:
- ALL questions MUST be in English
- ALL answers MUST be in English
- Use proper English grammar and appropriate vocabulary
- Maintain consistent language register throughout
- Adapt language complexity to content appropriately"""

        content_specific = {
            "academic": """
- Use precise academic vocabulary
- Focus on scientific and scholarly terminology
- Create questions that test conceptual understanding
- Include definitions and detailed explanations
- Emphasize theoretical frameworks and methodologies""",
            "technical": """
- Use appropriate technical terminology
- Create questions about processes and procedures
- Include cause-and-effect relationships
- Focus on technical accuracy and precision
- Emphasize practical applications and implementations""",
            "general": """
- Use clear and accessible English
- Create varied questions about main facts
- Include general comprehension questions
- Adapt language level to content complexity
- Focus on practical knowledge and understanding""",
        }

        specific_instructions = content_specific.get(content_type, content_specific["general"])

        template = (
            base_instructions
            + "\n\n"
            + specific_instructions
            + """

FLASHCARD REQUIREMENTS:
- Each flashcard must have exactly these fields: "question", "answer", "card_type"
- card_type must be either "qa" (question-answer) or "cloze" (cloze deletion)
- For cloze cards, use {{c1::text}} format in the question field
- Aim for 10-50 flashcards depending on content richness
- Prioritize quality over quantity

EXAMPLE VALID JSON OUTPUT:
[
  {
    "question": "What is the capital of France?",
    "answer": "Paris",
    "card_type": "qa"
  },
  {
    "question": "The capital of France is {{c1::Paris}}",
    "answer": "Paris",
    "card_type": "cloze"
  }
]

TEXT TO PROCESS:
{text}

JSON ARRAY:"""
        )

        return template

    @staticmethod
    def _get_french_template(content_type: str) -> str:
        """Get French prompt template."""
        base_instructions = """Vous êtes un expert en création de cartes mémoire (flashcards) pour l'apprentissage \
efficace et la rétention à long terme.

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
- Incluez des définitions et des explications détaillées
- Mettez l'accent sur les cadres théoriques et les méthodologies""",
            "technical": """
- Utilisez la terminologie technique française appropriée
- Créez des questions sur les processus et procédures
- Incluez des relations de cause à effet
- Privilégiez la précision technique
- Mettez l'accent sur les applications pratiques et les implémentations""",
            "general": """
- Utilisez un français accessible et clair
- Créez des questions variées sur les faits principaux
- Incluez des questions de compréhension générale
- Adaptez le niveau de langue au contenu
- Concentrez-vous sur les connaissances pratiques""",
        }

        specific_instructions = content_specific.get(content_type, content_specific["general"])

        template = (
            base_instructions
            + "\n\n"
            + specific_instructions
            + """

EXIGENCES DES CARTES MÉMOIRE:
- Chaque carte mémoire doit avoir exactement ces champs: "question", "answer", "card_type"
- card_type doit être soit "qa" (question-réponse) soit "cloze" (suppression à trous)
- Pour les cartes cloze, utilisez le format {{c1::texte}} dans le champ question
- Visez 10-50 cartes mémoire selon la richesse du contenu
- Privilégiez la qualité à la quantité

EXEMPLE DE SORTIE JSON VALIDE:
[
  {
    "question": "Quelle est la capitale de la France ?",
    "answer": "Paris",
    "card_type": "qa"
  },
  {
    "question": "La capitale de la France est {{c1::Paris}}",
    "answer": "Paris",
    "card_type": "cloze"
  }
]

TEXTE À TRAITER:
{text}

TABLEAU JSON:"""
        )

        return template

    @staticmethod
    def _get_italian_template(content_type: str) -> str:
        """Get Italian prompt template."""
        base_instructions = """Sei un esperto nella creazione di flashcard per l'apprendimento 
        efficace e la ritenzione a lungo termine.

REGOLE CRITICHE DI FORMATTAZIONE JSON:
- La tua risposta deve essere SOLO un array JSON valido, nient'altro
- Nessun testo esplicativo prima o dopo il JSON
- Usa virgolette doppie per tutte le stringhe
- Escapa le virgolette all'interno delle stringhe con barre inverse
- Assicurati che tutti gli oggetti JSON siano correttamente chiusi con virgole tra di loro
- L'ultimo oggetto dell'array NON deve avere una virgola finale

ISTRUZIONI IMPORTANTI:
1. Analizza il testo fornito e identifica i concetti, fatti e relazioni più importanti
2. Crea un mix di carte domanda-risposta e carte con cancellazione cloze
3. Concentrati sulle informazioni chiave che sarebbero preziose per la ritenzione a lungo termine
4. Formula domande chiare, specifiche e non ambigue IN ITALIANO
5. Assicurati che le risposte siano concise ma complete IN ITALIANO
6. Crea cancellazioni cloze per termini importanti, date e concetti

REQUISITI LINGUISTICI CRITICI:
- TUTTE le domande DEVONO essere in italiano
- TUTTE le risposte DEVONO essere in italiano
- Usa grammatica italiana corretta e vocabolario appropriato
- Rispetta gli accordi di genere e numero
- Adatta il registro linguistico al contenuto"""

        content_specific = {
            "academic": """
- Usa vocabolario accademico preciso
- Privilegia la terminologia scientifica italiana
- Crea domande che testano la comprensione concettuale
- Includi definizioni e spiegazioni dettagliate
- Enfatizza i quadri teorici e le metodologie""",
            "technical": """
- Usa la terminologia tecnica italiana appropriata
- Crea domande sui processi e le procedure
- Includi relazioni causa-effetto
- Privilegia la precisione tecnica
- Enfatizza le applicazioni pratiche e le implementazioni""",
            "general": """
- Usa italiano accessibile e chiaro
- Crea domande varie sui fatti principali
- Includi domande di comprensione generale
- Adatta il livello linguistico al contenuto
- Concentrati sulla conoscenza pratica""",
        }

        specific_instructions = content_specific.get(content_type, content_specific["general"])

        template = (
            base_instructions
            + "\n\n"
            + specific_instructions
            + """

REQUISITI DELLE FLASHCARD:
- Ogni flashcard deve avere esattamente questi campi: "question", "answer", "card_type"
- card_type deve essere "qa" (domanda-risposta) o "cloze" (cancellazione cloze)
- Per le carte cloze, usa il formato {{c1::testo}} nel campo domanda
- Punta a 10-50 flashcard a seconda della ricchezza del contenuto
- Privilegia la qualità rispetto alla quantità

ESEMPIO DI OUTPUT JSON VALIDO:
[
  {
    "question": "Qual è la capitale della Francia?",
    "answer": "Parigi",
    "card_type": "qa"
  },
  {
    "question": "La capitale della Francia è {{c1::Parigi}}",
    "answer": "Parigi",
    "card_type": "cloze"
  }
]

TESTO DA ELABORARE:
{text}

ARRAY JSON:"""
        )

        return template

    @staticmethod
    def _get_german_template(content_type: str) -> str:
        """Get German prompt template."""
        base_instructions = """Sie sind ein Experte für die Erstellung von Karteikarten für effektives Lernen und \
langfristige Behaltung.

KRITISCHE JSON-FORMATIERUNGSREGELN:
- Ihre Antwort muss NUR ein gültiges JSON-Array sein, nichts anderes
- Kein erklärender Text vor oder nach dem JSON
- Verwenden Sie doppelte Anführungszeichen für alle Strings
- Escapen Sie Anführungszeichen innerhalb von Strings mit Backslashes
- Stellen Sie sicher, dass alle JSON-Objekte ordnungsgemäß mit Kommas zwischen ihnen geschlossen sind
- Das letzte Objekt im Array sollte KEIN nachfolgendes Komma haben

WICHTIGE ANWEISUNGEN:
1. Analysieren Sie den bereitgestellten Text und identifizieren Sie die wichtigsten Konzepte, Fakten und Beziehungen
2. Erstellen Sie eine Mischung aus Frage-Antwort-Karten und Lückentext-Karten (Cloze Deletion)
3. Konzentrieren Sie sich auf Schlüsselinformationen, die für die langfristige Behaltung wertvoll wären
4. Formulieren Sie klare, spezifische und eindeutige Fragen AUF DEUTSCH
5. Stellen Sie sicher, dass die Antworten prägnant aber vollständig AUF DEUTSCH sind
6. Erstellen Sie Lückentexte für wichtige Begriffe, Daten und Konzepte

KRITISCHE SPRACHANFORDERUNGEN:
- ALLE Fragen MÜSSEN auf Deutsch sein
- ALLE Antworten MÜSSEN auf Deutsch sein
- Verwenden Sie korrekte deutsche Grammatik und angemessenes Vokabular
- Beachten Sie Genus-, Numerus- und Kasuskongruenz
- Passen Sie das Sprachregister an den Inhalt an"""

        content_specific = {
            "academic": """
- Verwenden Sie präzises akademisches Vokabular
- Bevorzugen Sie deutsche wissenschaftliche Terminologie
- Erstellen Sie Fragen, die das konzeptuelle Verständnis testen
- Schließen Sie Definitionen und detaillierte Erklärungen ein
- Betonen Sie theoretische Rahmen und Methodologien""",
            "technical": """
- Verwenden Sie angemessene deutsche Fachterminologie
- Erstellen Sie Fragen zu Prozessen und Verfahren
- Schließen Sie Ursache-Wirkungs-Beziehungen ein
- Bevorzugen Sie technische Genauigkeit
- Betonen Sie praktische Anwendungen und Implementierungen""",
            "general": """
- Verwenden Sie zugängliches und klares Deutsch
- Erstellen Sie vielfältige Fragen zu Hauptfakten
- Schließen Sie allgemeine Verständnisfragen ein
- Passen Sie das Sprachniveau an die Inhaltskomplexität an
- Konzentrieren Sie sich auf praktisches Wissen""",
        }

        specific_instructions = content_specific.get(content_type, content_specific["general"])

        template = (
            base_instructions
            + "\n\n"
            + specific_instructions
            + """

KARTEIKARTEN-ANFORDERUNGEN:
- Jede Karteikarte muss genau diese Felder haben: "question", "answer", "card_type"
- card_type muss entweder "qa" (Frage-Antwort) oder "cloze" (Lückentext) sein
- Für Cloze-Karten verwenden Sie das Format {{c1::Text}} im Fragefeld
- Streben Sie 10-50 Karteikarten an, je nach Inhaltsreichtum
- Priorisieren Sie Qualität vor Quantität

BEISPIEL GÜLTIGER JSON-OUTPUT:
[
  {
    "question": "Was ist die Hauptstadt von Frankreich?",
    "answer": "Paris",
    "card_type": "qa"
  },
  {
    "question": "Die Hauptstadt von Frankreich ist {{c1::Paris}}",
    "answer": "Paris",
    "card_type": "cloze"
  }
]

ZU VERARBEITENDER TEXT:
{text}

JSON-ARRAY:"""
        )

        return template

    @staticmethod
    def validate_template_parameters(language: str, content_type: str) -> bool:
        """
        Validate that the provided language and content_type are supported.

        Args:
            language: Target language
            content_type: Type of content

        Returns:
            True if parameters are valid, False otherwise
        """
        supported_languages = ["english", "french", "italian", "german", "en", "fr", "it", "de"]
        supported_content_types = ["academic", "technical", "general"]

        language = language.lower().strip()
        content_type = content_type.lower().strip()

        return language in supported_languages and content_type in supported_content_types

    @staticmethod
    def get_supported_languages() -> list[str]:
        """Get list of supported languages."""
        return ["english", "french", "italian", "german"]

    @staticmethod
    def get_supported_content_types() -> list[str]:
        """Get list of supported content types."""
        return ["academic", "technical", "general"]
