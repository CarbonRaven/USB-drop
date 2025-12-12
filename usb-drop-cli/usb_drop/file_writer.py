"""USB file operations for USB Drop CLI."""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def find_usb_drives() -> List[Path]:
    """Find mounted USB drives.

    Returns a list of paths to mounted USB drives.
    Platform-specific detection.
    """
    drives = []

    # macOS - look in /Volumes
    volumes_path = Path("/Volumes")
    if volumes_path.exists():
        for volume in volumes_path.iterdir():
            if volume.is_dir() and volume.name != "Macintosh HD":
                # Check if it looks like a USB drive
                # (not a network share, not the boot volume)
                if not volume.name.startswith("."):
                    drives.append(volume)

    # Linux - look in /media and /mnt
    for media_path in [Path("/media"), Path("/mnt")]:
        if media_path.exists():
            for user_dir in media_path.iterdir():
                if user_dir.is_dir():
                    for mount in user_dir.iterdir():
                        if mount.is_dir():
                            drives.append(mount)

    # Windows - check drive letters
    if os.name == "nt":
        import string
        for letter in string.ascii_uppercase:
            drive_path = Path(f"{letter}:\\")
            if drive_path.exists() and letter not in ["C"]:
                drives.append(drive_path)

    return drives


def extract_zip_to_usb(zip_path: Path, usb_path: Path, clear_existing: bool = False):
    """Extract a ZIP file to a USB drive.

    Args:
        zip_path: Path to the ZIP file
        usb_path: Path to the USB drive mount point
        clear_existing: Whether to clear existing files on the drive
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    if not usb_path.exists():
        raise FileNotFoundError(f"USB drive not found: {usb_path}")

    if clear_existing:
        console.print(f"[yellow]Clearing existing files on {usb_path}...[/yellow]")
        for item in usb_path.iterdir():
            if item.name.startswith("."):
                continue  # Skip hidden files
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Extracting files...", total=None)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(usb_path)

        progress.update(task, completed=True, description="Files extracted!")

    console.print(f"[green]Files written to {usb_path}[/green]")


def download_and_extract(
    api_client,
    drive_id: str,
    usb_path: Path,
    clear_existing: bool = False,
):
    """Download drive ZIP from API and extract to USB.

    Args:
        api_client: The API client instance
        drive_id: ID of the drive to download
        usb_path: Path to the USB drive mount point
        clear_existing: Whether to clear existing files on the drive
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading drive files...", total=None)

        # Download to temp file
        response = api_client.download_drive(drive_id)

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp_path = Path(tmp.name)

        progress.update(task, description="Download complete!")

    try:
        extract_zip_to_usb(tmp_path, usb_path, clear_existing)
    finally:
        tmp_path.unlink()


def verify_usb_contents(usb_path: Path) -> dict:
    """Verify USB contents and return a summary.

    Args:
        usb_path: Path to the USB drive mount point

    Returns:
        Dictionary with file counts and sizes
    """
    total_files = 0
    total_size = 0
    file_types = {}

    for root, dirs, files in os.walk(usb_path):
        for file in files:
            if file.startswith("."):
                continue
            file_path = Path(root) / file
            total_files += 1
            total_size += file_path.stat().st_size

            ext = file_path.suffix.lower() or "(no extension)"
            file_types[ext] = file_types.get(ext, 0) + 1

    return {
        "total_files": total_files,
        "total_size": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "file_types": file_types,
    }


def list_usb_contents(usb_path: Path, max_depth: int = 2) -> List[str]:
    """List USB contents as a tree.

    Args:
        usb_path: Path to the USB drive mount point
        max_depth: Maximum depth to traverse

    Returns:
        List of formatted file paths
    """
    contents = []

    def _walk(path: Path, depth: int, prefix: str = ""):
        if depth > max_depth:
            return

        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

        for i, item in enumerate(items):
            if item.name.startswith("."):
                continue

            is_last = i == len(items) - 1
            connector = "\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 "
            extension = "    " if is_last else "\u2502   "

            if item.is_dir():
                contents.append(f"{prefix}{connector}[bold]{item.name}/[/bold]")
                _walk(item, depth + 1, prefix + extension)
            else:
                size = item.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size / 1024:.1f} KB"
                contents.append(f"{prefix}{connector}{item.name} ({size_str})")

    _walk(usb_path, 0)
    return contents
