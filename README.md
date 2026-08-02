# Image Snapshot - Map Capture Web App

Browser-based version of the Image Snapshot map-capture tool. Upload a photo
(or a whole folder of photos), and for each one it reads the GPS location
embedded in the photo's EXIF metadata, captures a map snapshot of that area,
and saves it as a PNG or SVG file.

This is a **local** web app: the Flask backend runs on your own machine, so
"Browse..." buttons open real native Windows file/folder dialogs (not a
browser upload box) and the output folder can be anywhere on your machine,
exactly like the desktop version.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in a browser.

## How it works

1. **Choose upload mode** - single image, or a whole folder for bulk upload.
2. **Select image or folder** - click Browse to open a native picker.
   Detected images (and their EXIF GPS coordinates, if any) appear in a table.
3. Images with no GPS EXIF data (common with WhatsApp photos, screenshots, or
   re-saved images) show as "manual entry needed" - type latitude/longitude
   directly into the table, or leave both blank to skip that image.
4. **Export options** - choose PNG or SVG output, and a map zoom level (1-19).
5. **Choose output folder** - click Browse to pick where captured maps get
   saved, anywhere on your machine.
6. Click **Capture Map(s)**. Progress and per-file status show in the log.

### Naming

Each output file reuses the original image's name with an `_map` suffix,
e.g. `IMG_0001.jpg` -> `IMG_0001_map.png`. Name collisions in the output
folder get a numeric suffix (`IMG_0001_map_1.png`).

### PNG vs SVG

Map tiles (from OpenStreetMap) are raster images, so there's no native
vector map data to export. The PNG option saves the rendered map tile
directly. The SVG option wraps that same raster image inside a valid SVG
container, so it opens as an `.svg` file, but it is not a hand-drawn vector
graphic.

### Requirements

- Internet access (map tiles are fetched live from OpenStreetMap).
- Supported image formats: JPG, JPEG, PNG, TIF, TIFF, BMP, WEBP.
