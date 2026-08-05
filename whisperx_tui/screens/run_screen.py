from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Log, Static

from whisperx_tui.config import RunParams
from whisperx_tui.runner import run_whisperx


class RunScreen(Screen[None]):
    def __init__(self, params: RunParams) -> None:
        super().__init__()
        self.params = params

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static(f"Transcribing: {self.params.audio_path.name}", id="run-summary"),
            Log(id="run-log"),
            Static("Running...", id="run-status"),
            Button("Done", id="done-button", disabled=True),
            id="run-body",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._run(), exclusive=True)

    async def _run(self) -> None:
        log = self.query_one("#run-log", Log)
        status = self.query_one("#run-status", Static)
        try:
            async for line in run_whisperx(self.params):
                log.write_line(line)
        except Exception as exc:
            status.update(f"Failed: {exc}")
        else:
            outputs = self._output_files()
            if outputs:
                listing = "\n".join(f"  - {path}" for path in outputs)
                status.update(f"Done. Output files:\n{listing}")
            else:
                status.update("Done, but no output files were found -- check the log above.")
        finally:
            self.query_one("#done-button", Button).disabled = False

    def _output_files(self) -> list[Path]:
        stem = self.params.audio_path.stem
        return sorted(self.params.output_dir.glob(f"{stem}.*"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "done-button":
            self.dismiss()
