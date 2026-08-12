import json
import re
from pathlib import Path
from typing import Optional

import torch
from .config import *
from .schemas import QwenOutput
from .utils import clean_model_json


class QwenEngine:
    def __init__(self):
        self.device = f"cuda:{QWEN_GPU}"
        self.model = None
        self.processor = None
        self.load()

    def load(self):
        print(f"Loading Qwen3-VL on GPU {QWEN_GPU}...")

        try:
            from transformers import Qwen3VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
        except ImportError as exc:
            raise ImportError(
                "Transformers import failed. Install the compatible transformers package."
            ) from exc

        quantization = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

        model_options = {
            "quantization_config": quantization,
            "device_map": {"": QWEN_GPU},
            "torch_dtype": torch.float16,
            "low_cpu_mem_usage": True,
            "trust_remote_code": True,
        }
        try:
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                QWEN_MODEL,
                attn_implementation="flash_attention_2",
                **model_options,
            )
        except (ImportError, RuntimeError) as exc:
            print(f"FlashAttention unavailable; using the standard attention implementation: {exc}")
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                QWEN_MODEL,
                **model_options,
            )

        self.processor = AutoProcessor.from_pretrained(
            QWEN_MODEL,
            trust_remote_code=True,
        )

        self.model.eval()
        print("Qwen3-VL loaded successfully.")

    def generate(
        self,
        text: str,
        genre: str,
        mood: str,
        language: str,
        image_path: Optional[Path] = None,
    ) -> dict:
        if not text and image_path is None:
            raise ValueError("No study material provided to Qwen.")

        prompt = self._build_prompt(text=text, genre=genre, mood=mood, language=language)

        content = [{"type": "text", "text": prompt}]
        if image_path is not None:
            content.insert(0, {"type": "image", "image": str(image_path)})
        messages = [{"role": "user", "content": content}]

        chat_text = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
        )
        image_inputs = video_inputs = None
        if image_path is not None:
            try:
                from qwen_vl_utils import process_vision_info
            except ImportError as exc:
                raise ImportError("qwen-vl-utils is required to process image study material.") from exc
            image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[chat_text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )

        inputs = {
            key: value.to(self.device) if hasattr(value, "to") else value
            for key, value in inputs.items()
        }

        with torch.inference_mode():
            generated = self.model.generate(
                **inputs,
                max_new_tokens=QWEN_MAX_TOKENS,
                temperature=QWEN_TEMPERATURE,
                top_p=QWEN_TOP_P,
                top_k=QWEN_TOP_K,
                do_sample=True,
                pad_token_id=self.processor.tokenizer.eos_token_id,
            )

        input_tokens = inputs["input_ids"].shape[-1]
        output_tokens = generated[0, input_tokens:]

        raw = self.processor.batch_decode(output_tokens, skip_special_tokens=True)[0]
        parsed = self._parse_json(raw)
        return parsed

    def _build_prompt(self, text: str, genre: str, mood: str, language: str) -> str:
        return f"""
You are ORPHEUS, an educational songwriting AI.

Your job is to transform the supplied educational material into a highly memorable educational song.

IMPORTANT:
- Preserve factual accuracy.
- Do not invent facts.
- Do not change formulas.
- Do not keep educational content dry.
- Prioritize the concepts the student needs to remember.
- Use repetition, chorus, and structure for memory.
- Validate that every important statement is supported by the source.

User preferences:
Genre: {genre}
Mood: {mood}
Language: {language}

Return ONLY valid JSON with this schema:
{{
  "title": "...",
  "subject": "...",
  "topic": "...",
  "difficulty": "...",
  "genre_tags": "...",
  "key_facts": ["..."],
  "learning_objectives": ["..."],
  "lyrics": "...",
  "music_prompt": "..."
}}

Lyrics should include YuE-friendly sections like [verse], [chorus], and [bridge].

Educational material:
{text}
""".strip()

    def _parse_json(self, raw_text: str) -> dict:
        cleaned = clean_model_json(raw_text)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Qwen did not return parseable JSON.")

        candidate = cleaned[start:end + 1]

        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as exc:
            repaired = self._repair_json(candidate)
            data = json.loads(repaired)

        return QwenOutput(**data).model_dump()

    def _repair_json(self, text: str) -> str:
        text = re.sub(r",\s*([}\]])", r"\1", text)
        text = re.sub(r"\n+", "\n", text)
        return text
