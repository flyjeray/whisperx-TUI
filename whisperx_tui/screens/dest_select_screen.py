from pathlib import Path

from textual.app import App
from textual_fspicker import SelectDirectory


async def pick_destination_folder(app: App, start_dir: Path | str = ".") -> Path | None:
    return await app.push_screen_wait(
        SelectDirectory(str(start_dir), title="Select destination folder")
    )
