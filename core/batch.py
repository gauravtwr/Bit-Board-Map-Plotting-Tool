"""Discover images and process them into exported map snapshots."""

import os
from dataclasses import dataclass

from .exif_gps import extract_gps
from .map_capture import capture_map_image, save_png, save_svg

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}

SUFFIX = "_map"


@dataclass
class ProcessResult:
    source_path: str
    status: str  # "done", "skipped", "error"
    message: str
    output_path: str = ""


def find_images(directory):
    """Return a sorted list of image file paths directly inside `directory`."""
    found = []
    for name in sorted(os.listdir(directory)):
        path = os.path.join(directory, name)
        if os.path.isfile(path) and os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS:
            found.append(path)
    return found


def get_gps_map(image_paths):
    """Return {image_path: (lat, lon) or None} using each image's EXIF data.

    Many real-world sources (WhatsApp, screenshots, downloaded images,
    social media re-uploads) strip GPS EXIF entirely, so None here means
    "no coordinate available yet", not an error -- callers can fill these
    in manually before processing.
    """
    return {path: extract_gps(path) for path in image_paths}


def _unique_output_path(output_dir, stem, ext):
    candidate = os.path.join(output_dir, f"{stem}{SUFFIX}{ext}")
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(output_dir, f"{stem}{SUFFIX}_{counter}{ext}")
        counter += 1
    return candidate


def capture_and_save(image_path, coords, output_dir, export_format, zoom=15, size=(800, 600)):
    """Capture the map area for `coords` (lat, lon) and save it for image_path.

    `coords` may be None (no GPS EXIF and nothing entered manually), in
    which case the image is reported as skipped.
    """
    stem = os.path.splitext(os.path.basename(image_path))[0]
    ext = ".png" if export_format.upper() == "PNG" else ".svg"

    if coords is None:
        return ProcessResult(
            source_path=image_path,
            status="skipped",
            message=(
                "No GPS data available (no EXIF location found, e.g. WhatsApp/"
                "downloaded images strip this, and no coordinates were entered manually)"
            ),
        )

    lat, lon = coords
    try:
        map_image = capture_map_image(lat, lon, zoom=zoom, width=size[0], height=size[1])
        output_path = _unique_output_path(output_dir, stem, ext)

        if export_format.upper() == "PNG":
            save_png(map_image, output_path)
        else:
            save_svg(map_image, output_path, size[0], size[1])

        return ProcessResult(
            source_path=image_path,
            status="done",
            message=f"Captured area at {lat:.6f}, {lon:.6f}",
            output_path=output_path,
        )
    except Exception as exc:
        return ProcessResult(
            source_path=image_path,
            status="error",
            message=str(exc),
        )


def process_batch(coords_map, output_dir, export_format, zoom=15, size=(800, 600), on_progress=None):
    """Process each (image_path -> coords) entry, calling on_progress(result) after each one."""
    os.makedirs(output_dir, exist_ok=True)
    results = []
    for path, coords in coords_map.items():
        result = capture_and_save(path, coords, output_dir, export_format, zoom=zoom, size=size)
        results.append(result)
        if on_progress:
            on_progress(result)
    return results
