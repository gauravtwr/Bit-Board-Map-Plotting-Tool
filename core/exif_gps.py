"""Extract GPS coordinates embedded in an image's EXIF metadata."""

from PIL import Image

GPS_IFD_TAG = 0x8825
GPS_LAT_REF = 1
GPS_LAT = 2
GPS_LON_REF = 3
GPS_LON = 4


def _dms_to_degrees(dms):
    degrees, minutes, seconds = dms
    return float(degrees) + float(minutes) / 60.0 + float(seconds) / 3600.0


def extract_gps(image_path):
    """Return (lat, lon) as floats, or None if the image has no GPS EXIF data."""
    try:
        with Image.open(image_path) as img:
            exif = img.getexif()
            gps_ifd = exif.get_ifd(GPS_IFD_TAG)
    except Exception:
        return None

    if not gps_ifd or GPS_LAT not in gps_ifd or GPS_LON not in gps_ifd:
        return None

    try:
        lat = _dms_to_degrees(gps_ifd[GPS_LAT])
        if gps_ifd.get(GPS_LAT_REF) == "S":
            lat = -lat

        lon = _dms_to_degrees(gps_ifd[GPS_LON])
        if gps_ifd.get(GPS_LON_REF) == "W":
            lon = -lon
    except Exception:
        return None

    return lat, lon
