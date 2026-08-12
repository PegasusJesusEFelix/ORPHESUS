from typing import List

from pydantic import BaseModel, Field, field_validator


class QwenOutput(BaseModel):
    title: str = Field(..., min_length=3)
    subject: str = Field(..., min_length=2)
    topic: str = Field(..., min_length=2)
    difficulty: str = Field(..., min_length=2)
    genre_tags: str = Field(..., min_length=3)
    key_facts: List[str] = Field(..., min_length=1)
    learning_objectives: List[str] = Field(..., min_length=1)
    lyrics: str = Field(..., min_length=20)
    music_prompt: str = Field(..., min_length=10)

    @field_validator("lyrics")
    @classmethod
    def validate_lyrics_structure(cls, value: str) -> str:
        normalized = value.lower()
        if "[chorus]" not in normalized or "[verse]" not in normalized:
            raise ValueError("Lyrics must contain at least one [verse] and one [chorus] section.")
        if value.count("[") != value.count("]"):
            raise ValueError("Lyrics section tags are malformed.")
        return value.strip()

    @field_validator("key_facts", "learning_objectives")
    @classmethod
    def validate_non_empty_items(cls, items: List[str]) -> List[str]:
        cleaned_items = []
        for item in items:
            if not item or not item.strip():
                raise ValueError("List items must not be empty.")
            cleaned_items.append(item.strip())
        return cleaned_items


class GenerateResponse(BaseModel):
    success: bool
    song_id: str
    title: str
    lyrics: str
    key_facts: List[str]
    learning_objectives: List[str]
    audio_url: str
    genre_tags: str
    music_prompt: str
    subject: str
    topic: str
    difficulty: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
