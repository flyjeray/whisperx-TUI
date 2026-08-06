from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static

from whisperx_tui.config import RunParams, load_last_dirs, save_last_dirs
from whisperx_tui.deps import is_ffmpeg_on_path, is_whisperx_importable
from whisperx_tui.screens.dest_select_screen import pick_destination_folder
from whisperx_tui.screens.file_select_screen import pick_audio_paths
from whisperx_tui.screens.params_screen import ParamsScreen
from whisperx_tui.screens.run_screen import RunScreen
from whisperx_tui.screens.setup_screen import SetupScreen


class WhisperXTUIApp(App[None]):
    TITLE = "whisperx-tui"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("o", "pick_file", "Add file/folder"),
        ("c", "clear_queue", "Clear queue"),
        ("d", "pick_dest", "Pick destination"),
        ("p", "pick_params", "Set parameters & run"),
    ]

    dest_dir: Path | None = None
    run_params: RunParams | None = None

    def __init__(self) -> None:
        super().__init__()
        self.queue: list[Path] = []
        self._last_audio_dir, self._last_dest_dir = load_last_dirs()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self._status_text(), id="placeholder")
        yield Footer()

    def on_mount(self) -> None:
        if not (is_ffmpeg_on_path() and is_whisperx_importable()):
            self.push_screen(SetupScreen())

    def _status_text(self) -> str:
        if self.queue:
            listing = "\n".join(f"  - {path.name}" for path in self.queue)
            queue_text = f"Queue ({len(self.queue)} file(s)):\n{listing}"
        else:
            queue_text = "Queue: (empty -- press o to add a file, or a whole folder)"
        lines = [
            queue_text,
            f"Destination: {self.dest_dir or '(none -- press d to pick)'}",
        ]
        if self.queue and self.dest_dir:
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

    def action_clear_queue(self) -> None:
        self.queue = []
        self._refresh_status()

    def action_pick_dest(self) -> None:
        self.run_worker(self._pick_dest(), exclusive=True)

    def action_pick_params(self) -> None:
        if not self.queue or self.dest_dir is None:
            return
        self.run_worker(self._pick_params(), exclusive=True)

    async def _pick_file(self) -> None:
        result = await pick_audio_paths(self, start_dir=self._last_audio_dir or Path.home())
        if result is None:
            return
        if not result:
            self.notify("No audio files found in that folder.", severity="warning")
            return
        already_queued = set(self.queue)
        added = [path for path in result if path not in already_queued]
        self.queue = self.queue + added
        self._last_audio_dir = result[0].parent
        save_last_dirs(self._last_audio_dir, self._last_dest_dir)
        self._refresh_status()
        if len(added) < len(result):
            self.notify(f"Added {len(added)} file(s); {len(result) - len(added)} already queued.")
        else:
            self.notify(f"Added {len(added)} file(s) to the queue.")

    async def _pick_dest(self) -> None:
        result = await pick_destination_folder(self, start_dir=self._last_dest_dir or Path.home())
        if result is not None:
            self.dest_dir = result
            self._last_dest_dir = result
            save_last_dirs(self._last_audio_dir, self._last_dest_dir)
            self._refresh_status()

    async def _pick_params(self) -> None:
        assert self.dest_dir is not None
        result = await self.push_screen_wait(ParamsScreen(self.queue, self.dest_dir))
        if not result:
            return
        self.run_params = result[-1]
        self.queue = []
        self._refresh_status()
        await self.push_screen_wait(RunScreen(result))
        self._refresh_status()


def main() -> None:
    WhisperXTUIApp().run()


if __name__ == "__main__":
    main()
