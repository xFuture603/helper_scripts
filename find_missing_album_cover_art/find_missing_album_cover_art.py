#!/usr/bin/env python3

"""
Scan album folders for missing cover art.

The script checks both physical cover image files (cover.jpg, folder.png, etc.)
and embedded artwork in audio files (MP3, FLAC, M4A, WAV, OGG, OPUS).
Users can optionally scan only for physical or embedded artwork.

Output is structured for easier readability, with album headers and a summary.
"""

import argparse
from pathlib import Path
from mutagen import File
from mutagen.id3 import ID3NoHeaderError

# Allowed image extensions for physical cover files
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif"]


def has_cover_image(album_dir: Path) -> bool:
    """Check if the folder contains a physical cover image file."""
    for ext in IMAGE_EXTENSIONS:
        for fname in ["cover" + ext, "folder" + ext, "front" + ext]:
            if (album_dir / fname).exists():
                return True

    for f in album_dir.iterdir():
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
            return True

    return False


def has_embedded_cover(album_dir: Path) -> bool:
    """Check if any audio file in the folder has embedded cover art."""
    audio_extensions = [".mp3", ".flac", ".m4a", ".wav", ".ogg", ".opus"]

    for audio_file in album_dir.glob("*.*"):
        if audio_file.suffix.lower() not in audio_extensions:
            continue

        try:
            f = File(audio_file)
            if f is None:
                continue

            # MP3 files with ID3 tags
            if f.__class__.__name__ == "MP3":
                if hasattr(f, "tags") and f.tags is not None:
                    apics = [tag for tag in f.tags.values() if tag.FrameID.startswith("APIC")]
                    if apics:
                        return True

            # FLAC files
            elif f.__class__.__name__ == "FLAC":
                if hasattr(f, "pictures") and f.pictures:
                    return True
                if hasattr(f.tags, "getall") and f.tags.getall("METADATA_BLOCK_PICTURE"):
                    return True

            # MP4/M4A files
            elif f.__class__.__name__ == "MP4":
                if "covr" in f.tags and f.tags["covr"]:
                    return True

        except (ID3NoHeaderError, AttributeError, TypeError):
            continue

    return False


def main():
    """Parse arguments and scan the music library for missing covers."""
    parser = argparse.ArgumentParser(
        description="Scan album folders for missing cover art."
    )
    parser.add_argument("music_root", type=str, help="Root path of your music library")
    parser.add_argument(
        "--physical", action="store_true", help="Scan for physical cover image files only"
    )
    parser.add_argument(
        "--embedded", action="store_true", help="Scan for embedded cover art only"
    )
    args = parser.parse_args()

    music_root = Path(args.music_root)
    if not music_root.exists():
        print(f"Path does not exist: {music_root}")
        return

    audio_extensions = [".mp3", ".flac", ".m4a", ".wav", ".ogg", ".opus"]
    missing_physical = []
    missing_embedded = []

    print(f"\nScanning music library at: {music_root}\n{'='*50}")

    for album_dir in music_root.rglob("*"):
        if not album_dir.is_dir():
            continue

        # Skip folders without audio files
        if not any(f.suffix.lower() in audio_extensions for f in album_dir.iterdir()):
            continue

        print(f"\nAlbum: {album_dir.name}")
        print("-" * (7 + len(album_dir.name)))

        physical_ok = has_cover_image(album_dir)
        embedded_ok = has_embedded_cover(album_dir)

        if args.physical:
            if physical_ok:
                print("Physical cover: ✅ Found")
            else:
                print("Physical cover: ❌ Missing")
                missing_physical.append(album_dir)
        elif args.embedded:
            if embedded_ok:
                print("Embedded cover: ✅ Found")
            else:
                print("Embedded cover: ❌ Missing")
                missing_embedded.append(album_dir)
        else:
            # Default: check both
            print(f"Physical cover: {'✅ Found' if physical_ok else '❌ Missing'}")
            print(f"Embedded cover: {'✅ Found' if embedded_ok else '❌ Missing'}")
            if not physical_ok:
                missing_physical.append(album_dir)
            if not embedded_ok:
                missing_embedded.append(album_dir)

    # Summary
    print("\n" + "="*50 + "\nScan Summary:")
    if missing_physical:
        print(f"\nAlbums missing physical covers ({len(missing_physical)}):")
        for album in missing_physical:
            print(f"- {album}")
    else:
        print("\nAll albums have physical covers ✅")

    if missing_embedded:
        print(f"\nAlbums missing embedded covers ({len(missing_embedded)}):")
        for album in missing_embedded:
            print(f"- {album}")
    else:
        print("\nAll albums have embedded covers ✅")

    print("\nScan complete.\n")


if __name__ == "__main__":
    main()
