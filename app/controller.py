from pathlib import Path

from .qwen_engine import QwenEngine
from .yue_engine import YuEEngine
from .utils import has_source_overlap, read_text_from_pdf, read_text_from_txt


class OrpheusController:
    def __init__(self):
        self.qwen = QwenEngine()
        self.yue = YuEEngine()
        self.results = {}

    @property
    def qwen_ready(self) -> bool:
        return self.qwen.model is not None

    @property
    def yue_ready(self) -> bool:
        return self.yue.ready

    def generate(self, text: str, genre: str, mood: str, language: str) -> dict:
        song_payload = self.qwen.generate(
            text=text,
            genre=genre,
            mood=mood,
            language=language,
        )
        self._validate_source_consistency(song_payload, text)
        return self._compose(song_payload)

    def _compose(self, song_payload: dict) -> dict:

        music_payload = self.yue.generate(
            genre_tags=song_payload["genre_tags"],
            lyrics=song_payload["lyrics"],
        )

        song_id = music_payload["song_id"]
        result = {
            "success": True,
            "song_id": song_id,
            "title": song_payload["title"],
            "lyrics": song_payload["lyrics"],
            "key_facts": song_payload["key_facts"],
            "learning_objectives": song_payload["learning_objectives"],
            "genre_tags": song_payload["genre_tags"],
            "music_prompt": song_payload["music_prompt"],
            "subject": song_payload["subject"],
            "topic": song_payload["topic"],
            "difficulty": song_payload["difficulty"],
            "audio_url": f"/api/audio/{song_id}",
        }

        self.results[song_id] = result
        return result

    def generate_from_file(self, path: Path, genre: str, mood: str, language: str) -> dict:
        extension = path.suffix.lower()
        if extension == ".txt":
            text = read_text_from_txt(path)
            image_path = None
        elif extension == ".pdf":
            text = read_text_from_pdf(path)
            image_path = None
        elif extension in {".png", ".jpg", ".jpeg", ".webp"}:
            text = ""
            image_path = path
        else:
            raise ValueError("Unsupported file type for extraction.")

        song_payload = self.qwen.generate(text=text, genre=genre, mood=mood, language=language, image_path=image_path)
        if text:
            self._validate_source_consistency(song_payload, text)
        return self._compose(song_payload)

    @staticmethod
    def _validate_source_consistency(song_payload: dict, source_text: str) -> None:
        if not source_text:
            return
        unsupported = [fact for fact in song_payload["key_facts"] if not has_source_overlap(fact, source_text)]
        if unsupported:
            raise ValueError(
                "ORPHEUS could not verify key facts against the supplied material. Please try again with clearer notes."
            )

    def get_result(self, song_id: str) -> dict | None:
        return self.results.get(song_id)
