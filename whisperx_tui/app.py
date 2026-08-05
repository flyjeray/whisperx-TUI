from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static

from whisperx_tui.config import RunParams
from whisperx_tui.deps import is_ffmpeg_on_path, is_whisperx_importable
from whisperx_tui.screens.dest_select_screen import pick_destination_folder
from whisperx_tui.screens.file_select_screen import pick_audio_file
from whisperx_tui.screens.params_screen import ParamsScreen
from whisperx_tui.screens.run_screen import RunScreen
from whisperx_tui.screens.setup_screen import SetupScreen


class WhisperXTUIApp(App[None]):
    TITLE = "whisperx-tui"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("o", "pick_file", "Pick audio file"),
        ("d", "pick_dest", "Pick destination"),
        ("p", "pick_params", "Set parameters & run"),
    ]

    audio_path: Path | None = None
    dest_dir: Path | None = None
    run_params: RunParams | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self._status_text(), id="placeholder")
        yield Footer()

    def on_mount(self) -> None:
        if not (is_ffmpeg_on_path() and is_whisperx_importable()):
            self.push_screen(SetupScreen())

    def _status_text(self) -> str:
        lines = [
            f"Audio file: {self.audio_path or '(none -- press o to pick)'}",
            f"Destination: {self.dest_dir or '(none -- press d to pick)'}",
        ]
        if self.audio_path and self.dest_dir:
            lines.append("Press p to set parameters and start transcription.")
        if self.run_params is not None:
            params = self.run_params
            lines.append(
                f"\nLast run: model={params.model}, language={params.language or 'auto'}, "
                f"diarize={params.diarize}"
            )
        return "\n".join(lines)

    def _refresh_status(self) -> None:
        self.query_one("#placeholder", Static).update(self._status_text())

    def action_pick_file(self) -> None:
        self.run_worker(self._pick_file(), exclusive=True)

    def action_pick_dest(self) -> None:
        self.run_worker(self._pick_dest(), exclusive=True)

    def action_pick_params(self) -> None:
        if self.audio_path is None or self.dest_dir is None:
            return
        self.run_worker(self._pick_params(), exclusive=True)

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

    async def _pick_params(self) -> None:
        assert self.audio_path is not None and self.dest_dir is not None
        result = await self.push_screen_wait(ParamsScreen(self.audio_path, self.dest_dir))
        self.run_params = result
        self._refresh_status()
        await self.push_screen_wait(RunScreen(result))
        self._refresh_status()


def main() -> None:
    WhisperXTUIApp().run()


if __name__ == "__main__":
    main()
