#!/usr/bin/env python3
"""
Analyse YouTube thumbnails using a vision LLM running on Sparta via Ollama.

Usage:
    # Scan folder directly (no manifest needed — good for quick tests)
    python analyse_thumbnails.py <thumbnails_dir> --question "Describe this image."

    # Use manifest.json for richer metadata (title, URL, etc.)
    python analyse_thumbnails.py <thumbnails_dir> --question "Describe this image." --source manifest

Options:
    --question TEXT     Question to ask about each image (required)
    --source MODE       Where to discover images: "folder" (default) or "manifest"
    --limit N           Only process N images this run (0 = all pending)
    --model NAME        Ollama model (default: qwen3-vl:8b-instruct-q8_0)
    --ollama-url URL    Ollama base URL (default: http://ollama.sparta.home)
    --output FILE       Output JSON path (default: <thumbnails_dir>/analysis_results.json)
"""

import argparse
import base64
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    sys.exit("requests not installed. Run: pip install requests")


DEFAULT_OLLAMA_URL = "http://ollama.sparta.home"
DEFAULT_MODEL = "qwen3-vl:8b-instruct-q8_0"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


# ---------------------------------------------------------------------------
# Image discovery — two interchangeable sources
# ---------------------------------------------------------------------------

def get_pending_from_folder(thumbs_path: Path, already_done: set) -> list[dict]:
    """Scan the directory for image files, skipping anything already analysed."""
    entries = []
    for f in sorted(thumbs_path.iterdir()):
        if f.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        vid_id = f.stem  # filename without extension
        if vid_id in already_done:
            continue
        entries.append({
            "id": vid_id,
            "title": None,
            "url": None,
            "thumbnail_path": str(f),
        })
    return entries


def get_pending_from_manifest(thumbs_path: Path, already_done: set) -> list[dict]:
    """Load image list from manifest.json, skipping anything already analysed."""
    manifest_path = thumbs_path / "manifest.json"
    if not manifest_path.exists():
        sys.exit(f"No manifest.json found in {thumbs_path}. Run yt_thumbnails.py first.")

    with open(manifest_path) as f:
        manifest = json.load(f)

    videos = manifest.get("videos", {})
    if not videos:
        sys.exit("manifest.json has no videos. Nothing to analyse.")

    return [
        {
            "id": v["id"],
            "title": v.get("title"),
            "url": v.get("url"),
            "thumbnail_path": v["thumbnail_path"],
        }
        for v in videos.values()
        if v.get("thumbnail_path")
        and Path(v["thumbnail_path"]).exists()
        and v["id"] not in already_done
    ]


# ---------------------------------------------------------------------------
# Ollama helpers
# ---------------------------------------------------------------------------

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def ask_vision_model(ollama_url: str, model: str, image_b64: str, question: str) -> str:
    url = f"{ollama_url}/api/chat"
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": question,
                "images": [image_b64],
            }
        ],
    }
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Results persistence
# ---------------------------------------------------------------------------

def load_results(output_path: Path) -> dict:
    if output_path.exists():
        with open(output_path) as f:
            return json.load(f)
    return {"question": None, "model": None, "total_analysed": 0, "results": {}}


def save_results(output_path: Path, data: dict):
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Main analysis loop
# ---------------------------------------------------------------------------

def analyse(thumbnails_dir: str, question: str, source: str, limit: int,
            model: str, ollama_url: str, output_file: str):

    thumbs_path = Path(thumbnails_dir)
    output_path = Path(output_file) if output_file else thumbs_path / "analysis_results.json"
    results = load_results(output_path)
    results["question"] = question
    results["model"] = model

    already_done = set(results["results"].keys())

    if source == "manifest":
        pending = get_pending_from_manifest(thumbs_path, already_done)
    else:
        pending = get_pending_from_folder(thumbs_path, already_done)

    if not pending:
        print("Nothing new to analyse — all images already processed.")
        print(f"Results: {output_path}")
        return

    if limit:
        pending = pending[:limit]

    print(f"Ollama  : {ollama_url}")
    print(f"Model   : {model}")
    print(f"Source  : {source}")
    print(f"Question: {question}")
    print(f"To do   : {len(pending)} image(s)")
    print(f"Output  : {output_path}")
    print()

    for i, item in enumerate(pending, 1):
        vid_id = item["id"]
        label = item["title"] or vid_id
        thumb = item["thumbnail_path"]

        print(f"[{i}/{len(pending)}] {label[:70]}")

        try:
            image_b64 = encode_image(thumb)
            answer = ask_vision_model(ollama_url, model, image_b64, question)
        except requests.exceptions.ConnectionError:
            print(f"  ERROR: Cannot reach Ollama at {ollama_url}. Check VPN/network.")
            break
        except requests.exceptions.Timeout:
            print(f"  ERROR: Timed out on {vid_id}. Skipping.")
            results["results"][vid_id] = {
                "id": vid_id, "title": item["title"], "url": item["url"],
                "thumbnail_path": thumb, "answer": None, "error": "timeout",
                "analysed_at": datetime.utcnow().isoformat() + "Z",
            }
            save_results(output_path, results)
            continue
        except Exception as e:
            print(f"  ERROR: {e}")
            break

        print(f"  {answer[:120]}{'...' if len(answer) > 120 else ''}")

        results["results"][vid_id] = {
            "id": vid_id,
            "title": item["title"],
            "url": item["url"],
            "thumbnail_path": thumb,
            "answer": answer,
            "error": None,
            "analysed_at": datetime.utcnow().isoformat() + "Z",
        }
        results["total_analysed"] = len(results["results"])
        results["last_run"] = datetime.utcnow().isoformat() + "Z"
        save_results(output_path, results)

    print(f"\nDone. {results['total_analysed']} total analysed.")
    print(f"Results saved to: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Analyse images with a local vision LLM.")
    parser.add_argument("thumbnails_dir", help="Directory containing image files")
    parser.add_argument("--question", required=True, help='Prompt to send with each image')
    parser.add_argument("--source", choices=["folder", "manifest"], default="folder",
                        help="Image source: 'folder' scans directory directly, 'manifest' uses manifest.json (default: folder)")
    parser.add_argument("--limit", type=int, default=0, help="Max images to process this run (0 = all pending)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model (default: {DEFAULT_MODEL})")
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help=f"Ollama base URL (default: {DEFAULT_OLLAMA_URL})")
    parser.add_argument("--output", default="", help="Output JSON path (default: <dir>/analysis_results.json)")
    args = parser.parse_args()

    analyse(
        thumbnails_dir=args.thumbnails_dir,
        question=args.question,
        source=args.source,
        limit=args.limit,
        model=args.model,
        ollama_url=args.ollama_url,
        output_file=args.output,
    )


if __name__ == "__main__":
    main()
