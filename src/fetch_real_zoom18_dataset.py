import os
import json
import math
import io
import urllib.request
import concurrent.futures
import numpy as np
from PIL import Image
import cv2

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile

# Agricultural hubs in Karawang & Indramayu
LOCATIONS = [
    # Karawang (Lumbung Padi Pantura)
    ('Karawang_Rawamerta', -6.1852, 107.3241),
    ('Karawang_Kutawaluya', -6.1320, 107.3450),
    ('Karawang_Cilamaya', -6.2280, 107.5610),
    ('Karawang_Tempuran', -6.1720, 107.4520),
    ('Karawang_Jayakerta', -6.0950, 107.2850),
    ('Karawang_Lemahabang', -6.2235, 107.4120),
    ('Karawang_Cibuaya', -6.0750, 107.3620),
    ('Karawang_Pedes', -6.1150, 107.4350),
    # Indramayu (Sentra Padi Jawa Barat)
    ('Indramayu_Losarang', -6.3850, 108.1620),
    ('Indramayu_Kandanghaur', -6.3250, 108.1150),
    ('Indramayu_Sukra', -6.2950, 107.9850),
    ('Indramayu_Anjatan', -6.3750, 107.9750),
    ('Indramayu_Terisi', -6.4520, 108.1250),
    ('Indramayu_Gabuswetan', -6.4450, 108.1950)
]

def fetch_single_tile(item):
    name, lat, lon, tx, ty, z = item
    url = f"https://mt1.google.com/vt/lyrs=s&x={tx}&y={ty}&z={z}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = resp.read()
            if len(data) > 2000:
                img = Image.open(io.BytesIO(data)).convert("RGB")
                arr = np.array(img)
                hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
                gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
                lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                
                h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
                mud_water = float(np.mean(v < 60) * 100)
                veg = float(np.mean((h >= 18) & (h <= 85) & (s >= 40)) * 100)
                yellow = float(np.mean((h >= 18) & (h <= 38) & (s >= 45)) * 100)
                dry_soil = float(np.mean((s < 45) & (v >= 60) & (v <= 200)) * 100)
                glare = float(np.mean((v > 215) & (s < 35)) * 100)
                
                return {
                    'name': name, 'x': tx, 'y': ty, 'zoom': z,
                    'mud_water': mud_water, 'veg': veg, 'yellow': yellow,
                    'dry_soil': dry_soil, 'glare': glare, 'sharpness': float(lap_var),
                    'img': img
                }
    except Exception:
        pass
    return None

def collect_tiles(zoom=18):
    work_items = []
    for name, lat, lon in LOCATIONS:
        x0, y0 = deg2num(lat, lon, zoom)
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                work_items.append((name, lat, lon, x0 + dx, y0 + dy, zoom))
    
    print(f"Mengunduh {len(work_items)} kandidat tile satelit Zoom {zoom} secara paralel...")
    collected = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        for res in executor.map(fetch_single_tile, work_items):
            if res is not None:
                collected.append(res)
    print(f"Berhasil mengumpulkan {len(collected)} tile satelit Zoom {zoom} valid.")
    return collected

if __name__ == "__main__":
    tiles = collect_tiles(18)
    muddy = [t for t in tiles if t['mud_water'] >= 15]
    veggie = [t for t in tiles if t['veg'] >= 40]
    dry = [t for t in tiles if t['dry_soil'] >= 40]
    print(f"Tile Kaya Lumpur/Air (>=15%): {len(muddy)}")
    print(f"Tile Kaya Kanopi Padi (>=40%): {len(veggie)}")
    print(f"Tile Tanah Olah/Kering (>=40%): {len(dry)}")
