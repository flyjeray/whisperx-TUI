from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static

from whisperx_tui.deps import is_ffmpeg_on_path, is_whisperx_importable
from whisperx_tui.screens.setup_screen import SetupScreen


class WhisperXTUIApp(App[None]):
    TITLE = "whisperx-tui"
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "Dependencies OK. The main flow (file picker, parameters, run "
            "screen) isn't built yet -- press q to quit.",
            id="placeholder",
        )
        yield Footer()

    def on_mount(self) -> None:
        if not (is_ffmpeg_on_path() and is_whisperx_importable()):
            self.push_screen(SetupScreen())


def main() -> None:
    WhisperXTUIApp().run()


if __name__ == "__main__":
    main()
