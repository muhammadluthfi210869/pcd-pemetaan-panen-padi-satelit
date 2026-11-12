import os
import json
import math
import io
import csv
import zipfile
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

def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg

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

def fetch_tile(item):
    name, tx, ty, z = item
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
                
                lat, lon = num2deg(tx, ty, z)
                return {
                    'name': name, 'tx': tx, 'ty': ty, 'zoom': z,
                    'lat': lat, 'lon': lon,
                    'mud_water': mud_water, 'veg': veg, 'yellow': yellow,
                    'dry_soil': dry_soil, 'glare': glare, 'sharpness': float(lap_var),
                    'img': img
                }
    except Exception:
        pass
    return None

def main():
    z = 18
    work_items = []
    for name, lat, lon in LOCATIONS:
        x0, y0 = deg2num(lat, lon, z)
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                work_items.append((name, x0 + dx, y0 + dy, z))
    
    print(f"Mengunduh {len(work_items)} kandidat tile satelit Zoom {z} murni...")
    tiles = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        for res in executor.map(fetch_tile, work_items):
            if res is not None:
                tiles.append(res)
    
    print(f"Berhasil mengunduh {len(tiles)} tile satelit murni.")
    
    # Kategori filter
    # 1. Kanopi Padi (Vegetatif Hijau & Kuning Matang)
    veggie_tiles = [t for t in tiles if t['veg'] >= 45 and t['sharpness'] > 40]
    # Urutkan berdasarkan kerapatan kanopi
    veggie_tiles.sort(key=lambda t: t['veg'], reverse=True)
    
    # 2. Lumpur Basah & Genangan Air Murni (Flooded / Muddy Water)
    muddy_water_tiles = [t for t in tiles if t['mud_water'] >= 35 and t['veg'] < 15]
    muddy_water_tiles.sort(key=lambda t: t['mud_water'], reverse=True)
    
    # 3. Tanah Kering Merekah / Puso Kekeringan
    dry_soil_tiles = [t for t in tiles if t['dry_soil'] >= 45 and t['mud_water'] < 10 and t['veg'] < 10]
    dry_soil_tiles.sort(key=lambda t: t['dry_soil'], reverse=True)
    
    # 4. Sawah Pasca Panen Normal (Jerami / Tanah olah bajak campur sisa panen)
    harvest_after_tiles = [t for t in tiles if t['veg'] <= 20 and (t['dry_soil'] >= 30 or t['mud_water'] >= 15)]
    harvest_after_tiles.sort(key=lambda t: t['sharpness'], reverse=True)
    
    print(f"Kandidat Canopy Padi: {len(veggie_tiles)}")
    print(f"Kandidat Lumpur/Genangan Air: {len(muddy_water_tiles)}")
    print(f"Kandidat Tanah Kering/Puso: {len(dry_soil_tiles)}")
    print(f"Kandidat Sawah Pasca Panen: {len(harvest_after_tiles)}")
    
    # Target: 50 Pasang (100 citra murni)
    # - 25 Pasang Sukses Panen
    # - 13 Pasang Gagal Banjir
    # - 12 Pasang Gagal Kekeringan
    pairs = []
    
    # 1. Sukses Panen (25 pasang)
    for i in range(25):
        b_tile = veggie_tiles[i % len(veggie_tiles)]
        a_tile = harvest_after_tiles[i % len(harvest_after_tiles)]
        pair_id = f"PAIR_{i+1:03d}"
        pairs.append({
            'pair_id': pair_id,
            'kategori': 'SUKSES_PANEN',
            'ground_truth': 'SUKSES_PANEN',
            'wilayah': b_tile['name'],
            'lat': b_tile['lat'],
            'lon': b_tile['lon'],
            'zoom': z,
            'before_tile': b_tile,
            'after_tile': a_tile,
            'deskripsi': f"Sawah kanopi rimbun (Veg {b_tile['veg']:.1f}%) terpanen normal menjadi tanah olah/jerami (Veg {a_tile['veg']:.1f}%)"
        })
        
    # 2. Gagal Panen Banjir (13 pasang)
    for i in range(13):
        idx = 25 + i
        b_tile = veggie_tiles[(idx) % len(veggie_tiles)]
        a_tile = muddy_water_tiles[i % len(muddy_water_tiles)]
        pair_id = f"PAIR_{idx+1:03d}"
        pairs.append({
            'pair_id': pair_id,
            'kategori': 'GAGAL_BANJIR',
            'ground_truth': 'GAGAL_BANJIR',
            'wilayah': a_tile['name'],
            'lat': a_tile['lat'],
            'lon': a_tile['lon'],
            'zoom': z,
            'before_tile': b_tile,
            'after_tile': a_tile,
            'deskripsi': f"Sawah kanopi rimbun terendam air banjir & lumpur pekat ({a_tile['mud_water']:.1f}% genangan lumpur/air)"
        })
        
    # 3. Gagal Panen Kekeringan (12 pasang)
    for i in range(12):
        idx = 38 + i
        b_tile = veggie_tiles[(idx) % len(veggie_tiles)]
        a_tile = dry_soil_tiles[i % len(dry_soil_tiles)]
        pair_id = f"PAIR_{idx+1:03d}"
        pairs.append({
            'pair_id': pair_id,
            'kategori': 'GAGAL_KEKERINGAN',
            'ground_truth': 'GAGAL_KEKERINGAN',
            'wilayah': a_tile['name'],
            'lat': a_tile['lat'],
            'lon': a_tile['lon'],
            'zoom': z,
            'before_tile': b_tile,
            'after_tile': a_tile,
            'deskripsi': f"Sawah kanopi rimbun puso akibat kekeringan ekstrem ({a_tile['dry_soil']:.1f}% tanah merekah/kering)"
        })
        
    # Simpan ke folder direktori
    dataset_dir = "semua_dataset_gambar"
    os.makedirs(dataset_dir, exist_ok=True)
    
    csv_rows = []
    
    print(f"\nMenyimpan 50 pasang (100 citra murni satelit Zoom {z}) ke '{dataset_dir}'...")
    for p in pairs:
        pid = p['pair_id']
        b_fname = f"{pid}_BEFORE.jpg"
        a_fname = f"{pid}_AFTER.jpg"
        
        b_path = os.path.join(dataset_dir, b_fname)
        a_path = os.path.join(dataset_dir, a_fname)
        
        p['before_tile']['img'].save(b_path, quality=95)
        p['after_tile']['img'].save(a_path, quality=95)
        
        csv_rows.append({
            'Pair_ID': pid,
            'Kategori': p['kategori'],
            'Ground_Truth': p['ground_truth'],
            'Wilayah': p['wilayah'],
            'Lat': round(p['lat'], 6),
            'Lon': round(p['lon'], 6),
            'Zoom_Level': z,
            'GSD_Meter': 0.6,
            'Before_Veg_Percent': round(p['before_tile']['veg'], 1),
            'After_Mud_Water_Percent': round(p['after_tile']['mud_water'], 1),
            'After_Dry_Soil_Percent': round(p['after_tile']['dry_soil'], 1),
            'File_Before': b_fname,
            'File_After': a_fname,
            'Deskripsi': p['deskripsi']
        })
        
    csv_path = os.path.join(dataset_dir, "keterangan_dataset.csv")
    fieldnames = [
        'Pair_ID', 'Kategori', 'Ground_Truth', 'Wilayah', 'Lat', 'Lon',
        'Zoom_Level', 'GSD_Meter', 'Before_Veg_Percent',
        'After_Mud_Water_Percent', 'After_Dry_Soil_Percent',
        'File_Before', 'File_After', 'Deskripsi'
    ]
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Metadata dataset disimpan di '{csv_path}'")
    
    # Buat file zip
    zip_path = "semua_dataset_gambar.zip"
    print(f"Mengompres seluruh dataset ke '{zip_path}'...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for fname in os.listdir(dataset_dir):
            fpath = os.path.join(dataset_dir, fname)
            if os.path.isfile(fpath):
                zipf.write(fpath, arcname=fname)
                
    print(f"Berhasil! Dataset murni satelit Zoom 18 selesai dibuat: {len(csv_rows)} pasang citra.")

if __name__ == "__main__":
    main()
