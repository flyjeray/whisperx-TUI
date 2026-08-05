import dataclasses
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static, Switch

from whisperx_tui.config import CPU_COMPUTE_TYPES, MODEL_SIZES, OUTPUT_FORMATS, RunParams, TASKS

_DEFAULTS = {f.name: f.default for f in dataclasses.fields(RunParams)}


class ParamsScreen(Screen[RunParams]):
    def __init__(self, audio_path: Path, output_dir: Path) -> None:
        super().__init__()
        self.audio_path = audio_path
        self.output_dir = output_dir

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(
            Static(f"Audio: {self.audio_path}"),
            Static(f"Destination: {self.output_dir}"),
            Label("Model"),
            Select(
                ((m, m) for m in MODEL_SIZES),
                value=_DEFAULTS["model"],
                allow_blank=False,
                id="model",
            ),
            Label("Language (blank = auto-detect)"),
            Input(placeholder="e.g. ru, en", id="language"),
            Label("Task"),
            Select(
                ((t, t) for t in TASKS),
                value=_DEFAULTS["task"],
                allow_blank=False,
                id="task",
            ),
            Label("Compute type (CPU only: int8 is faster, float32 is more precise)"),
            Select(
                ((c, c) for c in CPU_COMPUTE_TYPES),
                value=_DEFAULTS["compute_type"],
                allow_blank=False,
                id="compute_type",
            ),
            Label("Batch size"),
            Input(value=str(_DEFAULTS["batch_size"]), type="integer", id="batch_size"),
            Label("Output format"),
            Select(
                ((f, f) for f in OUTPUT_FORMATS),
                value=_DEFAULTS["output_format"],
                allow_blank=False,
                id="output_format",
            ),
            Horizontal(
                Label("Diarize (label speakers)"),
                Switch(value=_DEFAULTS["diarize"], id="diarize"),
            ),
            Vertical(
                Label("Hugging Face token (required for diarization)"),
                Input(placeholder="hf_...", password=True, id="hf_token"),
                Label("Min speakers (optional)"),
                Input(placeholder="e.g. 2", type="integer", id="min_speakers"),
                Label("Max speakers (optional)"),
                Input(placeholder="e.g. 4", type="integer", id="max_speakers"),
                id="diarize-fields",
            ),
            Button("Start transcription", id="start-button", variant="primary"),
            id="params-body",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#diarize-fields").display = bool(_DEFAULTS["diarize"])

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id == "diarize":
            self.query_one("#diarize-fields").display = event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-button":
            self.dismiss(self._build_run_params())

    def _input_value(self, widget_id: str) -> str:
        return self.query_one(f"#{widget_id}", Input).value.strip()

    def _select_value(self, widget_id: str) -> str:
        value = self.query_one(f"#{widget_id}", Select).value
        assert isinstance(value, str)
        return value

    def _build_run_params(self) -> RunParams:
        diarize = self.query_one("#diarize", Switch).value
        batch_size_raw = self._input_value("batch_size") or str(_DEFAULTS["batch_size"])
        min_speakers_raw = self._input_value("min_speakers")
        max_speakers_raw = self._input_value("max_speakers")

        return RunParams(
            audio_path=self.audio_path,
            output_dir=self.output_dir,
            model=self._select_value("model"),
            language=self._input_value("language") or None,
            task=self._select_value("task"),
            compute_type=self._select_value("compute_type"),
            batch_size=int(batch_size_raw),
            output_format=self._select_value("output_format"),
            diarize=diarize,
            hf_token=(self._input_value("hf_token") or None) if diarize else None,
            min_speakers=int(min_speakers_raw) if diarize and min_speakers_raw else None,
            max_speakers=int(max_speakers_raw) if diarize and max_speakers_raw else None,
        )
