#!/usr/bin/env python3
"""
Download thumbnails from a YouTube channel incrementally.

Usage:
    python yt_thumbnails.py <channel_url> [--batch-size N] [--output-dir DIR]

Each run downloads up to --batch-size thumbnails (default 25) and records
progress in archive.txt so the next run continues from where it left off.
A manifest.json is updated after each run with video metadata + thumbnail paths.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

try:
    import yt_dlp
except ImportError:
    sys.exit("yt-dlp not installed. Run: pip install yt-dlp")


def load_manifest(manifest_path: Path) -> dict:
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return {"channel": None, "total_downloaded": 0, "videos": {}}


def save_manifest(manifest_path: Path, manifest: dict):
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def download_thumbnails(channel_url: str, output_dir: str, batch_size: int):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    archive_path = out / "archive.txt"
    manifest_path = out / "manifest.json"
    manifest = load_manifest(manifest_path)

    # Track newly downloaded videos in this run
    downloaded_this_run = []

    def progress_hook(d):
        # yt-dlp fires this for thumbnail writes too
        if d.get("status") == "finished":
            info = d.get("info_dict", {})
            video_id = info.get("id")
            if not video_id:
                return

            # Find the thumbnail file that was written
            thumbnail_file = None
            for ext in ("jpg", "webp", "png"):
                candidate = out / f"{video_id}.{ext}"
                if candidate.exists():
                    thumbnail_file = str(candidate)
                    break

            entry = {
                "id": video_id,
                "title": info.get("title"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "upload_date": info.get("upload_date"),
                "channel": info.get("channel"),
                "thumbnail_path": thumbnail_file,
                "downloaded_at": datetime.utcnow().isoformat() + "Z",
            }
            manifest["videos"][video_id] = entry
            if manifest["channel"] is None:
                manifest["channel"] = info.get("channel") or info.get("uploader")
            downloaded_this_run.append(video_id)

    ydl_opts = {
        "skip_download": True,
        "writethumbnail": True,
        # Prefer jpg; convert webp → jpg if ffmpeg is available
        "postprocessors": [{"key": "FFmpegThumbnailsConvertor", "format": "jpg"}],
        "outtmpl": str(out / "%(id)s.%(ext)s"),
        "download_archive": str(archive_path),
        "max_downloads": batch_size,
        "progress_hooks": [progress_hook],
        # Suppress most output; keep errors
        "quiet": True,
        "no_warnings": False,
        "ignoreerrors": True,  # skip unavailable/private videos
    }

    print(f"Channel : {channel_url}")
    print(f"Output  : {out.resolve()}")
    print(f"Batch   : up to {batch_size} thumbnails")
    print(f"Archive : {archive_path}")
    print()

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([channel_url])
    except yt_dlp.utils.MaxDownloadsReached:
        # Expected — yt-dlp raises this when the batch limit is hit
        pass

    # Update manifest totals and save
    manifest["total_downloaded"] = len(manifest["videos"])
    manifest["last_run"] = datetime.utcnow().isoformat() + "Z"
    save_manifest(manifest_path, manifest)

    # Summary
    print(f"\nDone. Downloaded {len(downloaded_this_run)} thumbnail(s) this run.")
    print(f"Total in manifest: {manifest['total_downloaded']}")
    if archive_path.exists():
        with open(archive_path) as f:
            archived = sum(1 for _ in f)
        print(f"Archive entries  : {archived}")
    print(f"Manifest saved to: {manifest_path}")


def main():
    parser = argparse.ArgumentParser(description="Download YouTube channel thumbnails incrementally.")
    parser.add_argument("channel_url", help="YouTube channel URL (e.g. https://www.youtube.com/@ChannelName)")
    parser.add_argument("--batch-size", type=int, default=25, help="Max thumbnails to download per run (default: 25)")
    parser.add_argument("--output-dir", default="thumbnails", help="Directory to save thumbnails and metadata (default: thumbnails/)")
    args = parser.parse_args()

    download_thumbnails(args.channel_url, args.output_dir, args.batch_size)


if __name__ == "__main__":
    main()
