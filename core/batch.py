"""Capture a map snapshot for a single (name, coordinate) pair, entirely in memory.

This app is stateless by design: uploaded images are only ever read once
(to pull GPS EXIF data) and never written to disk, so it can run on any
host without local filesystem access to the end user's machine.
"""

import os
from dataclasses import dataclass, field

from .map_capture import capture_map_image, png_bytes, svg_bytes

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}

SUFFIX = "_map"


@dataclass
class CaptureResult:
    name: str
    status: str  # "done", "skipped", "error"
    message: str
    output_name: str = ""
    data: bytes = field(default=b"", repr=False)


def capture_one(name, coords, export_format, zoom=15, size=(800, 600)):
    """Capture the map area for `coords` (lat, lon) and return the encoded bytes.

    `coords` may be None (no GPS EXIF and nothing entered manually), in
    which case the image is reported as skipped.
    """
    stem = os.path.splitext(name)[0]
    ext = ".png" if export_format.upper() == "PNG" else ".svg"
    output_name = f"{stem}{SUFFIX}{ext}"

    if coords is None:
        return CaptureResult(
            name=name,
            status="skipped",
            message=(
                "No GPS data available (no EXIF location found, e.g. WhatsApp/"
                "downloaded images strip this, and no coordinates were entered manually)"
            ),
        )

    lat, lon = coords
    try:
        image = capture_map_image(lat, lon, zoom=zoom, width=size[0], height=size[1])
        data = png_bytes(image) if export_format.upper() == "PNG" else svg_bytes(image, size[0], size[1])
        return CaptureResult(
            name=name,
            status="done",
            message=f"Captured area at {lat:.6f}, {lon:.6f}",
            output_name=output_name,
            data=data,
        )
    except Exception as exc:
        return CaptureResult(name=name, status="error", message=str(exc))
