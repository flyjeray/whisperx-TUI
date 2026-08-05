from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static

from whisperx_tui.deps import is_ffmpeg_on_path, is_whisperx_importable
from whisperx_tui.screens.dest_select_screen import pick_destination_folder
from whisperx_tui.screens.file_select_screen import pick_audio_file
from whisperx_tui.screens.setup_screen import SetupScreen


class WhisperXTUIApp(App[None]):
    TITLE = "whisperx-tui"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("o", "pick_file", "Pick audio file"),
        ("d", "pick_dest", "Pick destination"),
    ]

    audio_path: Path | None = None
    dest_dir: Path | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self._status_text(), id="placeholder")
        yield Footer()

    def on_mount(self) -> None:
        if not (is_ffmpeg_on_path() and is_whisperx_importable()):
            self.push_screen(SetupScreen())

    def _status_text(self) -> str:
        return (
            "Params/run screens aren't built yet.\n\n"
            f"Audio file: {self.audio_path or '(none -- press o to pick)'}\n"
            f"Destination: {self.dest_dir or '(none -- press d to pick)'}"
        )

    def _refresh_status(self) -> None:
        self.query_one("#placeholder", Static).update(self._status_text())

    def action_pick_file(self) -> None:
        self.run_worker(self._pick_file(), exclusive=True)

    def action_pick_dest(self) -> None:
        self.run_worker(self._pick_dest(), exclusive=True)

    async def _pick_file(self) -> None:
        result = await pick_audio_file(self, start_dir=Path.home())
        if result is not None:
            self.audio_path = result
            self._refresh_status()

    async def _pick_dest(self) -> None:
        result = await pick_destination_folder(self, start_dir=Path.home())
        if result is not None:
            self.dest_dir = result
            self._refresh_status()


def main() -> None:
    WhisperXTUIApp().run()


if __name__ == "__main__":
    main()
