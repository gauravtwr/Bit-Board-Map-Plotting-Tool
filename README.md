# Image Snapshot - Map Capture Web App

Browser-based version of the Image Snapshot map-capture tool. Upload a photo
(or several), and for each one it reads the GPS location embedded in the
photo's EXIF metadata, captures a map snapshot of that area, and sends back
a PNG or SVG file as a download.

This app is **stateless and deployable**: it never writes to the server's
filesystem. Uploaded images are read once in memory (to pull GPS EXIF data)
and discarded; captured maps are streamed straight back to the browser as a
download (a single file, or a ZIP for bulk uploads). That means it can run
on your own machine or be deployed to any host (Render, Railway, Fly.io,
etc.) without needing local filesystem access on either end.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in a browser. Set the `PORT` environment
variable to change the port (used automatically by most hosting platforms).

## How it works

1. **Choose upload mode** - single image, or bulk (multi-file or whole-folder
   select).
2. **Select image(s)** - a normal browser file picker. For bulk mode, "Select
   a folder..." works in Chrome/Edge; other browsers should use "Select
   files..." with multi-select. Detected images (and their EXIF GPS
   coordinates, if any) appear in a table.
3. Images with no GPS EXIF data (common with WhatsApp photos, screenshots, or
   re-saved images) show as "manual entry needed" - type latitude/longitude
   directly into the table, or leave both blank to skip that image.
4. **Export options** - choose PNG or SVG output, and a map zoom level (1-19).
5. Click **Capture & Download**. A single image downloads directly; a bulk
   batch downloads as one ZIP file containing every captured map plus a
   `results.txt` log of what was captured, skipped, or errored.

### Naming

Each output file reuses the original image's name with an `_map` suffix,
e.g. `IMG_0001.jpg` -> `IMG_0001_map.png`. Name collisions within a batch get
a numeric suffix (`IMG_0001_map_1.png`).

### PNG vs SVG

Map tiles (from OpenStreetMap) are raster images, so there's no native
vector map data to export. The PNG option returns the rendered map tile
directly. The SVG option wraps that same raster image inside a valid SVG
container, so it opens as an `.svg` file, but it is not a hand-drawn vector
graphic.

### Requirements

- Internet access (map tiles are fetched live from OpenStreetMap).
- Supported image formats: JPG, JPEG, PNG, TIF, TIFF, BMP, WEBP.

### Deploying

The included `app.py` runs Flask's development server, which is fine for
local use or quick testing but isn't meant for production traffic. For a
real deployment, run it behind a production WSGI server instead, e.g.:

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:$PORT app:app
```

#### Deploy to Render (free)

This repo includes a [`render.yaml`](render.yaml) blueprint, so Render can
provision everything automatically:

1. Go to [dashboard.render.com](https://dashboard.render.com) and sign in
   (GitHub login is easiest).
2. **New +** -> **Blueprint**, then pick this repository. Render reads
   `render.yaml` and pre-fills the service (Python, free plan, build/start
   commands) -- just click **Apply**.
3. Wait for the first build to finish, then open the `.onrender.com` URL
   Render gives you.

The free tier spins down after 15 minutes of inactivity and takes ~30
seconds to wake up on the next visit -- normal for a low-traffic tool, no
action needed.

Every subsequent `git push` to `main` auto-redeploys.
