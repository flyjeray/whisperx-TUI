import asyncio
import shutil
from collections.abc import AsyncIterator
from pathlib import Path

from whisperx_tui.config import RunParams, VENV_DIR, MODEL_CACHE_DIR


async def get_audio_duration_seconds(path: Path) -> float | None:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        return None

    process = await asyncio.create_subprocess_exec(
        ffprobe, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await process.communicate()
    if process.returncode != 0:
        return None

    try:
        return float(stdout.decode().strip())
    except ValueError:
        return None


async def extract_audio(video_path: Path, tmp_dir: Path) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required to extract audio from video files")

    # Keep the extracted file's stem matching the source video's, since
    # whisperx names its output files after whatever audio path it's given.
    output_path = tmp_dir / f"{video_path.stem}.wav"
    process = await asyncio.create_subprocess_exec(
        ffmpeg, "-y", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(output_path),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed to extract audio from {video_path.name}: "
            f"{stderr.decode(errors='replace').strip()}"
        )
    return output_path


def build_argv(params: RunParams) -> list[str]:
    argv = [
        str(VENV_DIR / "bin" / "whisperx"),
        str(params.audio_path),
        "--output_dir", str(params.output_dir),
        "--output_format", params.output_format,
        "--model", params.model,
        "--model_dir", str(MODEL_CACHE_DIR),
        "--task", params.task,
        "--device", "cpu",
        "--compute_type", params.compute_type,
        "--batch_size", str(params.batch_size),
        "--print_progress", "True",
    ]

    if params.language:
        argv += ["--language", params.language]

    if params.diarize:
        argv.append("--diarize")
        if params.hf_token:
            argv += ["--hf_token", params.hf_token]
        if params.min_speakers is not None:
            argv += ["--min_speakers", str(params.min_speakers)]
        if params.max_speakers is not None:
            argv += ["--max_speakers", str(params.max_speakers)]

    return argv


async def run_whisperx(params: RunParams) -> AsyncIterator[str]:
    argv = build_argv(params)
    process = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    assert process.stdout is not None

    async for raw_line in process.stdout:
        yield raw_line.decode(errors="replace").rstrip("\n")

    returncode = await process.wait()
    if returncode != 0:
        raise RuntimeError(f"whisperx exited with code {returncode}")
