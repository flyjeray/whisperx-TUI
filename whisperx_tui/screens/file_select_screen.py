from pathlib import Path

from textual.app import App
from textual_fspicker import FileOpen, Filters

AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma",
    ".mp4", ".mkv", ".mov",
}

AUDIO_FILTERS = Filters(
    ("Audio/video files", lambda path: path.suffix.lower() in AUDIO_EXTENSIONS),
    ("All files", lambda _path: True),
)


async def pick_audio_file(app: App, start_dir: Path | str = ".") -> Path | None:
    return await app.push_screen_wait(
        FileOpen(
            str(start_dir),
            title="Select audio file",
            filters=AUDIO_FILTERS,
            must_exist=True,
        )
    )
