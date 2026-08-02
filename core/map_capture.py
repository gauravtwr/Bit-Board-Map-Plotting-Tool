"""Render a map snapshot centered on a coordinate and save it as PNG or SVG."""

import base64
import io

from staticmap import StaticMap


TILE_REQUEST_TIMEOUT_SECONDS = 10

# OpenStreetMap's tile usage policy requires a distinct, identifying
# User-Agent and blocks/throttles generic or unattributed automated
# clients -- staticmap's default header ("User-Agent: StaticMap") gets
# flagged as exactly that, which is what caused requests to stall.
# See: https://operations.osmfoundation.org/policies/tiles/
TILE_REQUEST_HEADERS = {"User-Agent": "ImageSnapshotMapCapture/1.0 (local map-capture tool)"}


def capture_map_image(lat, lon, zoom=15, width=800, height=600):
    """Return a PIL Image of the area around (lat, lon). No marker is drawn.

    staticmap defaults to no request timeout, so a slow/unreachable tile
    server hangs forever instead of raising -- always pass a timeout so a
    network problem surfaces as an error within seconds.
    """
    renderer = StaticMap(
        width,
        height,
        tile_request_timeout=TILE_REQUEST_TIMEOUT_SECONDS,
        headers=TILE_REQUEST_HEADERS,
    )
    return renderer.render(zoom=zoom, center=[lon, lat])


def save_png(image, output_path):
    image.save(output_path, "PNG")


def save_svg(image, output_path, width, height):
    """Wrap the rendered raster map tile in an SVG container.

    OpenStreetMap tiles are raster images, so there is no true vector map
    to export here -- this embeds the PNG as a base64 <image> inside an
    SVG file, which keeps the .svg extension/format the user asked for
    while still being a valid, viewable file.
    """
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<image width="{width}" height="{height}" '
        f'href="data:image/png;base64,{encoded}"/>'
        f"</svg>"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
