import re
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Log, ProgressBar, Static

from whisperx_tui.config import RunParams
from whisperx_tui.runner import get_audio_duration_seconds, run_whisperx

_PROGRESS_RE = re.compile(r"Progress:\s*([\d.]+)%")
_TRANSCRIPT_TIME_RE = re.compile(r"Transcript: \[[\d.]+ --> ([\d.]+)\]")

# Transcription and alignment are the two stages that produce the transcript
# text/timing, so their progress is combined into one continuous 0-100 bar
# (0-50 while transcribing, 50-100 while aligning) -- that's what actually
# answers "how much of the file is done" from the user's point of view.
# Diarization (if enabled) runs after both and has no per-segment progress
# signal in whisperx itself, so it's shown as a distinct label instead.
#
# Whisperx's own "Progress: X%..." line is based on (segments done / total
# segments), which jumps in big, uneven steps when VAD segments vary a lot
# in length -- a single 2s segment counts the same as a single 58s one. Each
# "Transcript: [start --> end] ..." line during the transcribe stage carries
# a real timestamp though, so when the audio's duration is known (via
# ffprobe), that timestamp against total duration gives a truer, smoother
# percentage. Alignment has no per-segment timestamps in its output, so it
# still falls back to the segment-count number.
_STAGE_MARKERS = (
    ("Performing voice activity detection", "detect", "Detecting speech..."),
    ("Performing transcription", "transcribe", "Transcribing..."),
    ("Performing alignment", "align", "Aligning..."),
    ("Performing diarization", "diarize", "Diarizing speakers (no progress available)..."),
)


class RunScreen(Screen[None]):
    def __init__(self, params: RunParams) -> None:
        super().__init__()
        self.params = params
        self._stage = "detect"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static(f"Transcribing: {self.params.audio_path.name}", id="run-summary"),
            Static("Starting...", id="run-phase"),
            ProgressBar(total=100, id="run-progress", show_eta=False),
            Static("Running...", id="run-status"),
            Button("Show details", id="details-button"),
            Log(id="run-log"),
            Button("Done", id="done-button", disabled=True),
            id="run-body",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#run-log", Log).display = False
        self.run_worker(self._run(), exclusive=True)

    async def _run(self) -> None:
        log = self.query_one("#run-log", Log)
        status = self.query_one("#run-status", Static)
        phase = self.query_one("#run-phase", Static)
        progress_bar = self.query_one("#run-progress", ProgressBar)
        duration = await get_audio_duration_seconds(self.params.audio_path)
        try:
            async for line in run_whisperx(self.params):
                for marker, stage, label in _STAGE_MARKERS:
                    if marker in line:
                        self._stage = stage
                        phase.update(label)
                        break

                transcript_match = _TRANSCRIPT_TIME_RE.search(line)
                progress_match = _PROGRESS_RE.search(line)

                if self._stage == "align" and progress_match:
                    # No per-segment timestamps available during alignment,
                    # so this is the best signal there is.
                    progress_bar.update(progress=50 + float(progress_match.group(1)) / 2)
                elif self._stage == "transcribe" and duration and transcript_match:
                    end_time = float(transcript_match.group(1))
                    percent = min(100.0, (end_time / duration) * 100)
                    progress_bar.update(progress=percent / 2)
                elif self._stage == "transcribe" and not duration and progress_match:
                    # ffprobe unavailable -- fall back to the coarser
                    # segment-count metric rather than showing nothing.
                    progress_bar.update(progress=float(progress_match.group(1)) / 2)

                if not progress_match:
                    log.write_line(line)
        except Exception as exc:
            status.update(f"Failed: {exc} (see details below)")
            log.display = True
        else:
            phase.update("Finished")
            progress_bar.update(progress=100)
            outputs = self._output_files()
            if outputs:
                listing = "\n".join(f"  - {path}" for path in outputs)
                status.update(f"Done. Output files:\n{listing}")
            else:
                status.update("Done, but no output files were found -- check the log below.")
                log.display = True
        finally:
            self.query_one("#done-button", Button).disabled = False

    def _output_files(self) -> list[Path]:
        stem = self.params.audio_path.stem
        return sorted(self.params.output_dir.glob(f"{stem}.*"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "done-button":
            self.dismiss()
        elif event.button.id == "details-button":
            log = self.query_one("#run-log", Log)
            log.display = not log.display
            event.button.label = "Hide details" if log.display else "Show details"
