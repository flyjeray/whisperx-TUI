from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

from whisperx_tui.config import RunParams, load_last_dirs, save_last_dirs
from whisperx_tui.deps import is_ffmpeg_on_path, is_whisperx_importable
from whisperx_tui.screens.dest_select_screen import pick_destination_folder
from whisperx_tui.screens.file_select_screen import pick_audio_paths
from whisperx_tui.screens.params_screen import ParamsScreen
from whisperx_tui.screens.run_screen import RunScreen
from whisperx_tui.screens.setup_screen import SetupScreen


class WhisperXTUIApp(App[None]):
    TITLE = "whisperx-tui"
    CSS_PATH = "app.tcss"
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
        with Vertical(id="home-body"):
            with Vertical(id="queue-panel", classes="panel"):
                yield ListView(id="queue-list")
            with Vertical(id="dest-panel", classes="panel"):
                yield Static(self._dest_text(), id="dest-line")
            yield Static(self._hint_text(), id="hint-line", classes="hint")
            yield Static(self._last_run_text(), id="last-run-line")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#queue-panel").border_title = "Queue"
        self.query_one("#dest-panel").border_title = "Destination"
        self._refresh_queue()
        self._refresh_dest()
        if not (is_ffmpeg_on_path() and is_whisperx_importable()):
            self.push_screen(SetupScreen())

    def _dest_text(self) -> str:
        return str(self.dest_dir) if self.dest_dir else "(none -- press d to pick)"

    def _hint_text(self) -> str:
        if self.queue and self.dest_dir:
            return "Press p to set parameters and start transcription."
        missing = []
        if not self.queue:
            missing.append("add a file or folder (o)")
        if not self.dest_dir:
            missing.append("pick a destination (d)")
        return "Next: " + " and ".join(missing)

    def _last_run_text(self) -> str:
        if self.run_params is None:
            return ""
        params = self.run_params
        return (
            f"Last run: model={params.model}, language={params.language or 'auto'}, "
            f"diarize={params.diarize}"
        )

    def _refresh_queue(self) -> None:
        list_view = self.query_one("#queue-list", ListView)
        list_view.clear()
        if not self.queue:
            list_view.append(ListItem(Label("(empty -- press o to add a file, or a whole folder)", classes="hint")))
        else:
            for path in self.queue:
                list_view.append(ListItem(Label(f"♪ {path.name}")))
        self.query_one("#queue-panel").border_title = f"Queue ({len(self.queue)})"
        self._refresh_hint()

    def _refresh_dest(self) -> None:
        dest_line = self.query_one("#dest-line", Static)
        dest_line.update(self._dest_text())
        dest_line.set_class(self.dest_dir is not None, "status-ready")
        dest_line.set_class(self.dest_dir is None, "status-pending")
        self._refresh_hint()

    def _refresh_hint(self) -> None:
        hint = self.query_one("#hint-line", Static)
        hint.update(self._hint_text())
        hint.set_class(bool(self.queue and self.dest_dir), "status-ready")

    def _refresh_last_run(self) -> None:
        self.query_one("#last-run-line", Static).update(self._last_run_text())

    def action_pick_file(self) -> None:
        self.run_worker(self._pick_file(), exclusive=True)

    def action_clear_queue(self) -> None:
        self.queue = []
        self._refresh_queue()

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
        self._refresh_queue()
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
            self._refresh_dest()

    async def _pick_params(self) -> None:
        assert self.dest_dir is not None
        result = await self.push_screen_wait(ParamsScreen(self.queue, self.dest_dir))
        if not result:
            return
        self.run_params = result[-1]
        self.queue = []
        self._refresh_queue()
        self._refresh_last_run()
        await self.push_screen_wait(RunScreen(result))
        self._refresh_last_run()


def main() -> None:
    WhisperXTUIApp().run()


if __name__ == "__main__":
    main()
