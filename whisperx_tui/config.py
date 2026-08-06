import json
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "whisperx-tui"
APP_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
VENV_DIR = APP_DIR / "venv"
MODEL_CACHE_DIR = APP_DIR / "models"
STATE_FILE = APP_DIR / "state.json"

OUTPUT_FORMATS = ("all", "srt", "vtt", "txt", "tsv", "json")
CPU_COMPUTE_TYPES = ("int8", "float32")
MODEL_SIZES = ("tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo")
TASKS = ("transcribe", "translate")

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma"}
# Video files get their audio extracted via ffmpeg before being handed to
# whisperx -- see runner.extract_audio.
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov"}
MEDIA_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS


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


def load_last_dirs() -> tuple[Path | None, Path | None]:
    """Returns (last audio browse dir, last destination dir), skipping any that no longer exist."""
    try:
        data = json.loads(STATE_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return None, None

    def valid_dir(raw: object) -> Path | None:
        path = Path(raw) if raw else None
        return path if path and path.is_dir() else None

    return valid_dir(data.get("last_audio_dir")), valid_dir(data.get("last_dest_dir"))


def save_last_dirs(audio_dir: Path | None, dest_dir: Path | None) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(
            {
                "last_audio_dir": str(audio_dir) if audio_dir else None,
                "last_dest_dir": str(dest_dir) if dest_dir else None,
            }
        )
    )
