import asyncio

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Log, Static

from whisperx_tui.deps import (
    brew_install,
    is_ffmpeg_on_path,
    is_whisperx_importable,
    stream_pip_install,
)


class SetupScreen(Screen[None]):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static(self._missing_summary(), id="setup-summary"),
            Log(id="setup-log"),
            Button("Install", id="install-button", variant="primary"),
            id="setup-body",
            classes="panel",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#setup-body").border_title = "Setup required"

    def _missing_summary(self) -> str:
        missing = []
        if not is_ffmpeg_on_path():
            missing.append("ffmpeg")
        if not is_whisperx_importable():
            missing.append("whisperx")
        return (
            "This tool needs the following before it can transcribe audio:\n"
            f"  - {', '.join(missing)}\n\n"
            "Press Install to set them up now (this may take a few minutes)."
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "install-button":
            event.button.disabled = True
            self.run_worker(self.install_dependencies(), exclusive=True)

    async def install_dependencies(self) -> None:
        log = self.query_one("#setup-log", Log)
        try:
            if not is_ffmpeg_on_path():
                log.write_line("Installing ffmpeg via Homebrew...")
                await asyncio.to_thread(brew_install, "ffmpeg")
                log.write_line("ffmpeg installed.")

            if not is_whisperx_importable():
                log.write_line("Installing whisperx (this can take several minutes)...")
                async for line in stream_pip_install("whisperx"):
                    log.write_line(line)
        except Exception as exc:
            log.write_line(f"Setup failed: {exc}")
            return

        log.write_line("Setup complete.")
        self.dismiss()
