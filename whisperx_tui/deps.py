import asyncio
import importlib.util
import shutil
import subprocess
from collections.abc import AsyncIterator

from whisperx_tui.config import VENV_DIR


def is_ffmpeg_on_path() -> bool:
    return shutil.which("ffmpeg") is not None


def is_whisperx_importable() -> bool:
    return importlib.util.find_spec("whisperx") is not None


def brew_install(package: str) -> None:
    if shutil.which("brew") is None:
        raise RuntimeError(
            f"Homebrew is required to install '{package}' but was not found on PATH. "
            "Install it from https://brew.sh first."
        )
    subprocess.run(["brew", "install", package], check=True)


async def stream_pip_install(package: str) -> AsyncIterator[str]:
    process = await asyncio.create_subprocess_exec(
        str(VENV_DIR / "bin" / "pip"), "install", package,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    assert process.stdout is not None

    async for raw_line in process.stdout:
        yield raw_line.decode(errors="replace").rstrip("\n")

    returncode = await process.wait()
    if returncode != 0:
        raise RuntimeError(f"pip install {package} exited with code {returncode}")
