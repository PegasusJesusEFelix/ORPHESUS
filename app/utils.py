import json
import re
import uuid
from pathlib import Path
from typing import Optional

from PIL import Image

from .config import SUPPORTED_UPLOAD_EXTENSIONS


def make_uuid():
    return uuid.uuid4().hex


def read_text_from_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def read_text_from_pdf(path: Path) -> str:
    import fitz

    with fitz.open(path) as document:
        pages = [page.get_text().strip() for page in document if page.get_text().strip()]
    return "\n\n".join(pages).strip()


def load_image(path: Path) -> Image.Image:
    image = Image.open(path)
    return image.convert("RGB")


def clean_model_json(raw_text: str) -> str:
    text = raw_text.strip()
    text = re.sub(r"```json\s*", "", text, flags=re.I)
    text = re.sub(r"```\s*", "", text)
    return text


def safe_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def validate_upload_extension(filename: str) -> Optional[str]:
    extension = Path(filename).suffix.lower()
    return extension if extension in SUPPORTED_UPLOAD_EXTENSIONS else None


def ensure_readable_upload(path: Path) -> None:
    extension = path.suffix.lower()
    if extension == ".txt":
        if not read_text_from_txt(path):
            raise ValueError("The text file is empty or could not be read.")
    elif extension == ".pdf":
        if not read_text_from_pdf(path):
            raise ValueError("We could not find readable study text in that PDF.")
    else:
        with Image.open(path) as image:
            image.verify()


def has_source_overlap(claim: str, source: str) -> bool:
    """Reject claims with no meaningful vocabulary drawn from a text source."""
    tokens = lambda value: set(re.findall(r"[a-zA-Z0-9]{4,}", value.lower()))
    claim_tokens = tokens(claim)
    source_tokens = tokens(source)
    return bool(claim_tokens and source_tokens and claim_tokens & source_tokens)
