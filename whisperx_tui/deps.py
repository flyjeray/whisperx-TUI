import shutil
import subprocess


def is_ffmpeg_on_path() -> bool:
    return shutil.which("ffmpeg") is not None


def brew_install(package: str) -> None:
    if shutil.which("brew") is None:
        raise RuntimeError(
            f"Homebrew is required to install '{package}' but was not found on PATH. "
            "Install it from https://brew.sh first."
        )
    subprocess.run(["brew", "install", package], check=True)
