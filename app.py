"""Image Snapshot - Map Capture web app.

Run with: python app.py
Then open http://127.0.0.1:5000 in a browser.
"""

import os

from flask import Flask, jsonify, render_template, request

from core.batch import capture_and_save, find_images, get_gps_map
from native_dialogs import pick_file, pick_folder

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/pick-file", methods=["POST"])
def api_pick_file():
    path = pick_file()
    return jsonify({"path": path})


@app.route("/api/pick-folder", methods=["POST"])
def api_pick_folder():
    data = request.get_json(silent=True) or {}
    title = data.get("title") or "Select a folder"
    path = pick_folder(title=title)
    return jsonify({"path": path})


@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")
    path = data.get("path")

    if not path:
        return jsonify({"error": "No path provided"}), 400

    if mode == "single":
        if not os.path.isfile(path):
            return jsonify({"error": "Selected path is not a valid file"}), 400
        image_paths = [path]
    elif mode == "bulk":
        if not os.path.isdir(path):
            return jsonify({"error": "Selected path is not a valid folder"}), 400
        image_paths = find_images(path)
    else:
        return jsonify({"error": "mode must be 'single' or 'bulk'"}), 400

    if not image_paths:
        return jsonify({"items": []})

    gps_map = get_gps_map(image_paths)
    items = [
        {
            "path": p,
            "name": os.path.basename(p),
            "lat": coords[0] if coords else None,
            "lon": coords[1] if coords else None,
        }
        for p, coords in gps_map.items()
    ]
    return jsonify({"items": items})


@app.route("/api/capture-one", methods=["POST"])
def api_capture_one():
    data = request.get_json(silent=True) or {}
    path = data.get("path")
    lat = data.get("lat")
    lon = data.get("lon")
    output_dir = data.get("output_dir")
    export_format = data.get("format", "PNG")
    zoom = int(data.get("zoom", 15))

    if not path or not os.path.isfile(path):
        return jsonify({"error": "Invalid image path"}), 400
    if not output_dir:
        return jsonify({"error": "No output folder provided"}), 400

    coords = (float(lat), float(lon)) if lat is not None and lon is not None else None

    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as exc:
        return jsonify({"error": f"Could not create output folder: {exc}"}), 400

    result = capture_and_save(path, coords, output_dir, export_format, zoom=zoom)

    return jsonify(
        {
            "name": os.path.basename(result.source_path),
            "status": result.status,
            "message": result.message,
            "output_path": result.output_path,
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=False, use_reloader=False)
