# whisperx-tui

A terminal UI wrapper around whisperx, the speech-to-text/subtitle tool. Instead
of activating a venv and remembering command-line flags, you pick a file, pick
a destination folder, set a few parameters, and watch it transcribe.

It manages its own Python environment. On first run it will install Python via
Homebrew if it's missing, create a dedicated venv (kept separate from any other
Python project on your machine), and install whisperx and ffmpeg into it the
first time they're needed.

## Running it

Double-click whisperx-tui.app in Finder. It opens a Terminal window and
launches the app.

Or from the terminal:

    cd whisper-UI
    ./bootstrap.sh

Either way it's the same script underneath: checks for Python, sets up the
venv if it doesn't exist yet, and launches the app. On a clean machine the
very first run will take a few minutes since it has to download whisperx's
dependencies (mainly torch) and, later, the actual transcription models.

## Using it

o adds a file to the queue (or a whole folder of audio/video files at once),
c clears the queue, d picks a destination folder, p opens the parameters form
and runs the queue once you press Start -- files transcribe one after another
automatically. Video files have their audio extracted via ffmpeg first. The
run screen shows a progress bar tracking how much of the current file has
been transcribed, not a wall of log text -- press the details button if you
want to see the raw output, e.g. to see why something failed.

Parameters worth knowing about:

Model size trades speed for accuracy. Medium is the default because small
struggles noticeably on non-English audio. Language can be left blank for
auto-detect, or set explicitly (ru, en, etc). Diarization (speaker labels)
is off by default -- turning it on requires a Hugging Face token, since the
underlying model is gated behind accepting its license on huggingface.co.

## Status

The core flow works end to end: pick file, pick destination, set parameters,
run, get output files. Diarization is wired up but not tested against a real
gated model. There's no handling yet for things like picking an unwritable
destination folder beyond whatever error whisperx itself prints.
