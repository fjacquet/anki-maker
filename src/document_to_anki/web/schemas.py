from pydantic import BaseModel, Field


class FlashcardResponse(BaseModel):
    """Response model for flashcard data."""

    id: str
    question: str
    answer: str
    card_type: str
    source_file: str | None = None
    created_at: str


class ProcessingStatusResponse(BaseModel):
    """Response model for processing status."""

    session_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    message: str
    flashcard_count: int = 0
    errors: list[str] = Field(default_factory=list)


class FlashcardEditRequest(BaseModel):
    """Request model for editing flashcards."""

    question: str
    answer: str


class FlashcardCreateRequest(BaseModel):
    """Request model for creating flashcards."""

    question: str
    answer: str
    card_type: str
    source_file: str | None = None


class ExportRequest(BaseModel):
    """Request model for CSV export."""

    filename: str | None = "flashcards.csv"
