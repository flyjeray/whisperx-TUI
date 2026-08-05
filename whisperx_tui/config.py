from dataclasses import dataclass
from pathlib import Path

APP_NAME = "whisperx-tui"
APP_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
VENV_DIR = APP_DIR / "venv"
MODEL_CACHE_DIR = APP_DIR / "models"

OUTPUT_FORMATS = ("all", "srt", "vtt", "txt", "tsv", "json")
CPU_COMPUTE_TYPES = ("int8", "float32")


@dataclass
class RunParams:
    audio_path: Path
    output_dir: Path
    # "small" trails noticeably on non-English audio (verified: Russian
    # transcription quality picks up a lot going to "medium"); "small" is
    # still fine as a quick-preview option in the UI later.
    model: str = "medium"
    language: str | None = None
    task: str = "transcribe"
    compute_type: str = "int8"
    batch_size: int = 8
    output_format: str = "srt"
    diarize: bool = False
    hf_token: str | None = None
    min_speakers: int | None = None
    max_speakers: int | None = None
