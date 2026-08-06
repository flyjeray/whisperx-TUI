from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Button
from textual_fspicker import FileOpen, Filters
from textual_fspicker.parts import DirectoryNavigation

AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma",
    ".mp4", ".mkv", ".mov",
}

AUDIO_FILTERS = Filters(
    ("Audio/video files", lambda path: path.suffix.lower() in AUDIO_EXTENSIONS),
    ("All files", lambda _path: True),
)


class AudioFileOrFolderOpen(FileOpen):
    """FileOpen with an extra button to pick the whole browsed folder.

    textual_fspicker's own dialogs never return a directory (typing or
    clicking one just navigates into it), so an explicit button is the only
    way to let a folder itself be "selected" from this same dialog.
    """

    def _input_bar(self) -> ComposeResult:
        yield from super()._input_bar()
        yield Button("Select folder", id="select-folder")

    @on(Button.Pressed, "#select-folder")
    def _select_current_folder(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(result=self.query_one(DirectoryNavigation).location)


def _audio_files_in_folder(folder: Path) -> list[Path]:
    return sorted(
        (p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS),
        key=lambda p: p.name.lower(),
    )


async def pick_audio_paths(app: App, start_dir: Path | str = ".") -> list[Path] | None:
    """Let the user pick one audio file, or a folder to queue every audio file in it."""
    result = await app.push_screen_wait(
        AudioFileOrFolderOpen(
            str(start_dir),
            title="Select audio file (or 'Select folder' to queue a whole folder)",
            filters=AUDIO_FILTERS,
            must_exist=True,
        )
    )
    if result is None:
        return None
    if result.is_dir():
        return _audio_files_in_folder(result)
    return [result]
