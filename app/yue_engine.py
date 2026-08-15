import subprocess
import sys
import uuid
from pathlib import Path

from .config import *


class YuEEngine:
    def __init__(self):
        self.yue_dir = YUE_DIR
        self.inference_dir = self.yue_dir / "inference"
        self.infer_script = self.inference_dir / "infer.py"
        self.ready = self.infer_script.exists()

    def generate(self, genre_tags: str, lyrics: str) -> dict:
        if not self.ready:
            raise RuntimeError("YuE inference implementation is not available in the YuE directory.")

        song_id = uuid.uuid4().hex
        work_dir = TEMP_DIR / song_id
        work_dir.mkdir(parents=True, exist_ok=True)

        genre_file = work_dir / "genre.txt"
        lyrics_file = work_dir / "lyrics.txt"
        genre_file.write_text(genre_tags, encoding="utf-8")
        lyrics_file.write_text(lyrics, encoding="utf-8")

        output_dir = OUTPUT_DIR / song_id
        output_dir.mkdir(parents=True, exist_ok=True)

        command = [
            sys.executable,
            str(self.infer_script),
            "--cuda_idx",
            str(YUE_GPU),
            "--stage1_model",
            YUE_STAGE1,
            "--stage2_model",
            YUE_STAGE2,
            "--genre_txt",
            str(genre_file),
            "--lyrics_txt",
            str(lyrics_file),
            "--run_n_segments",
            str(YUE_RUN_SEGMENTS),
            "--stage2_batch_size",
            str(YUE_STAGE2_BATCH_SIZE),
            "--output_dir",
            str(output_dir),
            "--max_new_tokens",
            str(YUE_MAX_NEW_TOKENS),
            "--repetition_penalty",
            str(YUE_REPETITION_PENALTY),
        ]

        # Stream output to a log file instead of capturing into memory
        log_file = work_dir / "yue_run.log"
        with open(log_file, "w", encoding="utf-8") as lf:
            process = subprocess.run(
                command,
                cwd=str(self.inference_dir),
                stdout=lf,
                stderr=lf,
            )

        if process.returncode != 0:
            # include the tail of the log to help debugging without loading huge outputs
            tail = log_file.read_text(encoding="utf-8", errors="ignore")[-6000:]
            raise RuntimeError(
                "YuE generation failed. " + tail
            )

        audio_files = list(output_dir.rglob("*.wav"))
        if not audio_files:
            raise RuntimeError("YuE completed but produced no WAV output.")

        final_audio = OUTPUT_DIR / f"{song_id}.wav"
        audio_files[0].replace(final_audio)
        return {"song_id": song_id, "audio_path": str(final_audio)}
