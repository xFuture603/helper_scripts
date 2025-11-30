# Scan for missing Album Cover Art

This script scans your music library for missing album cover art, checking both physical image files (cover.jpg, folder.png, etc.) and embedded artwork in audio files (MP3, FLAC, M4A, WAV, OGG, OPUS). Currently it does not support all available metadata atoms for cover arts, but I've tried to cover most of them.

## Description

The script recursively scans all album folders in your music library and identifies albums that are missing cover art. It can check for:

Physical cover images in the folder, such as cover.jpg, folder.png, or any supported image file.

Embedded artwork in audio files, including MP3, FLAC, and M4A formats.

You can optionally limit the scan to only physical or embedded covers.

## Use Cases

Identify albums that are missing cover art in your music library.

Ensure all albums have either embedded artwork or a folder image.

Help organize and clean up your music collection before tagging or uploading.

## Requirements

- Python 3.12+

- mutagen python library

## Usage

The script can be run from the command line. You must specify the root path to your music library. Optional flags allow scanning only for physical or embedded artwork.

```bash
python3 find_missing_album_cover_art.py <music_root> [--physical] [--embedded]
```

## Arguments

<music_root>: Path to your music library.

`--physical`: Only scan for physical cover image files.

`--embedded`: Only scan for embedded artwork.

If neither `--physical` nor `--embedded` is specified, the script checks for both and reports albums missing any kind of cover.

## Example Output

```bash
Album: There Is Nothing Left To Lose
------------------------------------
Physical cover: ✅ Found
Embedded cover: ✅ Found
==================================================
Scan Summary:

All albums have physical covers ✅

Albums missing embedded covers (1):
- /music/Breaking Benjamin/Dark Before Dawn
```

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
