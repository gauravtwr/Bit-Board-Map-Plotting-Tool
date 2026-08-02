"""Image Snapshot - Map Capture web app (deployable, stateless).

Run with: python app.py
Then open http://127.0.0.1:5000 in a browser.

No server-side filesystem access is used: uploaded images are read once
in memory to pull GPS EXIF data, and captured maps are streamed straight
back to the browser as a download (a single file, or a ZIP for bulk
uploads). This means the app can be deployed to any host, not just run
on the same machine as the browser.
"""

import base64
import io
import json
import os
import zipfile

from flask import Flask, jsonify, render_template, request, send_file

from core.batch import IMAGE_EXTENSIONS, capture_one
from core.exif_gps import extract_gps

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB upload cap


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan", methods=["POST"])
def api_scan():
    files = request.files.getlist("images")
    if not files:
        return jsonify({"error": "No files were uploaded"}), 400

    items = []
    for index, file in enumerate(files):
        name = file.filename or f"image_{index}"
        ext = os.path.splitext(name)[1].lower()
        if ext not in IMAGE_EXTENSIONS:
            continue

        coords = extract_gps(file.stream)
        items.append(
            {
                "index": index,
                "name": name,
                "lat": coords[0] if coords else None,
                "lon": coords[1] if coords else None,
            }
        )

    return jsonify({"items": items})


def _unique_name(used_names, name):
    if name not in used_names:
        used_names.add(name)
        return name
    stem, ext = os.path.splitext(name)
    counter = 1
    while True:
        candidate = f"{stem}_{counter}{ext}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        counter += 1


@app.route("/api/capture-batch", methods=["POST"])
def api_capture_batch():
    data = request.get_json(silent=True) or {}
    items = data.get("items") or []
    export_format = data.get("format", "PNG")
    try:
        zoom = int(data.get("zoom", 15))
    except (TypeError, ValueError):
        zoom = 15

    if not items:
        return jsonify({"error": "No items to capture"}), 400

    results = []
    for item in items:
        name = item.get("name") or "image"
        lat = item.get("lat")
        lon = item.get("lon")
        coords = (float(lat), float(lon)) if lat is not None and lon is not None else None
        results.append(capture_one(name, coords, export_format, zoom=zoom))

    successes = [r for r in results if r.status == "done"]
    summary = {
        "done": len(successes),
        "skipped": sum(1 for r in results if r.status == "skipped"),
        "errors": sum(1 for r in results if r.status == "error"),
        "items": [
            {"name": r.name, "status": r.status, "message": r.message}
            for r in results
        ],
    }
    summary_header = base64.b64encode(json.dumps(summary).encode("utf-8")).decode("ascii")

    if not successes:
        return jsonify({"error": "No images could be captured", **summary}), 422

    if len(results) == 1:
        result = successes[0]
        mimetype = "image/png" if result.output_name.endswith(".png") else "image/svg+xml"
        response = send_file(
            io.BytesIO(result.data),
            mimetype=mimetype,
            as_attachment=True,
            download_name=result.output_name,
        )
        response.headers["X-Capture-Results"] = summary_header
        response.headers["Access-Control-Expose-Headers"] = "X-Capture-Results"
        return response

    used_names = set()
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for result in successes:
            zf.writestr(_unique_name(used_names, result.output_name), result.data)

        manifest_lines = [f"{r.name}: {r.status} - {r.message}" for r in results]
        zf.writestr("results.txt", "\n".join(manifest_lines))

    zip_buffer.seek(0)
    response = send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="bit-and-board-maps.zip",
    )
    response.headers["X-Capture-Results"] = summary_header
    response.headers["Access-Control-Expose-Headers"] = "X-Capture-Results"
    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
