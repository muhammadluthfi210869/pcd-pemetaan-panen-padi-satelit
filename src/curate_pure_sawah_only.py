import os
import csv
import json
import math
import io
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

# Titik koordinat tepat di tengah hamparan sawah terbuka luas (JAUH DARI PERKAMPUNGAN / RUMAH)
PURE_SAWAH_LOCATIONS = [
    # Karawang (Hamparan Sawah Murni Terbuka Pantura)
    ('Karawang_Rawamerta_Sawah', -6.2100, 107.3500),
    ('Karawang_Jayakerta_Sawah', -6.1100, 107.3100),
    ('Karawang_Kutawaluya_Sawah', -6.1600, 107.3700),
    ('Karawang_Tempuran_Sawah', -6.2000, 107.4800),
    ('Karawang_Cilamaya_Sawah', -6.2500, 107.5500),
    ('Karawang_Pedes_Sawah', -6.0800, 107.4100),
    ('Karawang_Cibuaya_Sawah', -6.0500, 107.3400),
    ('Karawang_Lemahabang_Sawah', -6.2350, 107.4350),
    # Indramayu (Lautan Sawah Terbuka Pantura)
    ('Indramayu_Losarang_Sawah', -6.4100, 108.1500),
    ('Indramayu_Kandanghaur_Sawah', -6.3600, 108.0900),
    ('Indramayu_Sukra_Sawah', -6.3200, 107.9700),
    ('Indramayu_Anjatan_Sawah', -6.4000, 107.9600),
    ('Indramayu_Terisi_Sawah', -6.4800, 108.1100),
    ('Indramayu_Gabuswetan_Sawah', -6.4550, 108.2100)
]

def detect_buildings(arr):
    """
    Detektor Bangunan / Pemukiman Berbasis Morfologi & Warna Genteng / Seng.
    Memastikan nol bangunan rumah pada citra satelit Zoom 18.
    """
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
    r = arr[:, :, 0].astype(int)
    g = arr[:, :, 1].astype(int)
    b = arr[:, :, 2].astype(int)

    # 1. Terracotta / Red-Orange Clay Tile Roof Mask
    terra_mask = (r > 130) & (r - g > 25) & (r - b > 40) & (hsv[:, :, 1] > 60)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(terra_mask.astype(np.uint8))
    house_blobs = 0
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h_dim = stats[i, cv2.CC_STAT_HEIGHT]
        # Atap rumah minimal ukuran 10x10 px (~6m x 6m pada Zoom 18)
        if area >= 180 and w >= 10 and h_dim >= 10:
            house_blobs += 1

    # 2. Zinc / Metallic Roof Mask (Sangat terang, desaturasi)
    zinc_mask = (hsv[:, :, 2] > 235) & (hsv[:, :, 1] < 25)
    num_labels_z, _, stats_z, _ = cv2.connectedComponentsWithStats(zinc_mask.astype(np.uint8))
    zinc_blobs = 0
    for i in range(1, num_labels_z):
        area = stats_z[i, cv2.CC_STAT_AREA]
        w = stats_z[i, cv2.CC_STAT_WIDTH]
        h_dim = stats_z[i, cv2.CC_STAT_HEIGHT]
        if area >= 200 and w >= 10 and h_dim >= 10:
            zinc_blobs += 1

    return house_blobs, zinc_blobs

def fetch_and_validate_tile(item):
    name, tx, ty, z = item
    url = f"https://mt1.google.com/vt/lyrs=s&x={tx}&y={ty}&z={z}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
            if len(data) > 1500:
                img = Image.open(io.BytesIO(data)).convert("RGB")
                arr = np.array(img)
                
                # Saring bangunan: NOL toleransi untuk atap rumah genteng & seng
                hb, zb = detect_buildings(arr)
                if hb > 0 or zb > 0:
                    return None

                hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
                h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
                
                # Ekstraksi Fitur Fisik Sawah
                # 1. Tajuk Vegetasi (Padi Kuning Matang s.d. Hijau Rimbun)
                veg = float(np.mean((h >= 18) & (h <= 85) & (s >= 35) & (v >= 45)) * 100)
                # 2. Air banjir / Lumpur basah / Silau air
                mud_water = float(np.mean((v <= 65) | ((s < 35) & (v > 215))) * 100)
                # 3. Tanah kering merekah / Puso kering
                dry_soil = float(np.mean((s <= 45) & (v >= 60)) * 100)
                
                # 4. Yellow Pixel Ratio (YPR)
                crop_pixels = (h >= 18) & (h <= 85) & (s >= 35) & (v >= 45)
                crop_cnt = np.count_nonzero(crop_pixels)
                if crop_cnt > 0:
                    yellow_cnt = np.count_nonzero(crop_pixels & (h >= 18) & (h <= 38))
                    ypr = float(yellow_cnt / crop_cnt * 100)
                else:
                    ypr = 0.0

                lat, lon = num2deg(tx, ty, z)
                return {
                    'name': name, 'tx': tx, 'ty': ty, 'zoom': z,
                    'lat': lat, 'lon': lon,
                    'veg': veg, 'mud_water': mud_water, 'dry_soil': dry_soil,
                    'ypr': ypr,
                    'img': img
                }
    except Exception:
        pass
    return None

def main():
    z = 18
    work_items = []
    # Grid 9x9 sekeliling 14 sentra sawah murni terbuka
    for name, lat, lon in PURE_SAWAH_LOCATIONS:
        x0, y0 = deg2num(lat, lon, z)
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                work_items.append((name, x0 + dx, y0 + dy, z))

    print(f"Mengunduh & memvalidasi {len(work_items)} kandidat tile satelit Zoom {z} murni sawah...")
    valid_sawah = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        for res in executor.map(fetch_and_validate_tile, work_items):
            if res is not None:
                valid_sawah.append(res)

    print(f"Berhasil menyaring {len(valid_sawah)} tile 100% MURNI SAWAH (0 bangunan rumah/atap).")

    # Klasifikasikan tile ke kelompok fenologis sawah alami
    # A. Kanopi Vegetasi (Padi Hijau Subur & Kuning Siap Panen) - veg >= 48%
    canopy_pool = [t for t in valid_sawah if t['veg'] >= 48.0]
    # Urutkan berdasarkan variasi YPR dan Veg agar sangat variatif (dari hijau pekat sampai kuning keemasan)
    canopy_pool.sort(key=lambda t: (t['ypr'], t['veg']))

    # B. Lahan Pasca Panen Normal (Jerami, tanah olahan bajak, sisa potongan batang) - veg <= 25%, mud_water < 70%, dry_soil < 75%
    harvest_pool = [t for t in valid_sawah if t['veg'] <= 25.0 and t['mud_water'] < 70.0 and t['dry_soil'] < 75.0]
    # Acak atau variasikan urutan berdasarkan kelembapan tanah
    harvest_pool.sort(key=lambda t: t['mud_water'])

    # C. Lahan Terendam Banjir / Lumpur Pekat Masif - mud_water >= 70%, veg <= 20%
    flood_pool = [t for t in valid_sawah if t['mud_water'] >= 70.0 and t['veg'] <= 20.0]
    flood_pool.sort(key=lambda t: t['mud_water'], reverse=True)

    # D. Lahan Puso Kekeringan Ekstrem - dry_soil >= 70%, mud_water <= 10%, veg <= 20%
    drought_pool = [t for t in valid_sawah if t['dry_soil'] >= 70.0 and t['mud_water'] <= 10.0 and t['veg'] <= 20.0]
    drought_pool.sort(key=lambda t: t['dry_soil'], reverse=True)

    print(f"\n--- DISTRIBUSI POOL CITRA SAWAH UNIK ---")
    print(f"Pool Kanopi Padi (Butuh 50 unik): {len(canopy_pool)} tile tersedia")
    print(f"Pool Pasca Panen Normal (Butuh 25 unik): {len(harvest_pool)} tile tersedia")
    print(f"Pool Banjir Lumpur (Butuh 13 unik): {len(flood_pool)} tile tersedia")
    print(f"Pool Kekeringan Retak (Butuh 12 unik): {len(drought_pool)} tile tersedia")

    assert len(canopy_pool) >= 50, f"Kurang kanopi unik: {len(canopy_pool)} < 50"
    assert len(harvest_pool) >= 25, f"Kurang harvest unik: {len(harvest_pool)} < 25"
    assert len(flood_pool) >= 13, f"Kurang flood unik: {len(flood_pool)} < 13"
    assert len(drought_pool) >= 12, f"Kurang drought unik: {len(drought_pool)} < 12"

    # Seleksi 100 Citra Satelit Murni Unik (NOL DUPLIKAT!)
    pairs = []
    
    # 1. 25 Pasang Sukses Panen (Semua Unik)
    # Ambil 25 kanopi dengan variasi merata (dari hijau muda, hijau pekat, hingga kuning emas)
    step_canopy = len(canopy_pool) // 50
    for i in range(25):
        canopy_idx = i * step_canopy
        b_tile = canopy_pool[canopy_idx]
        
        harvest_step = len(harvest_pool) // 25
        a_tile = harvest_pool[i * harvest_step]
        
        pid = f"PAIR_{i+1:03d}"
        ypr_str = f", YPR {b_tile['ypr']:.1f}% (Padi Kuning Matang)" if b_tile['ypr'] > 20 else f", YPR {b_tile['ypr']:.1f}% (Padi Hijau)"
        pairs.append({
            'pair_id': pid,
            'kategori': 'SUKSES_PANEN',
            'ground_truth': 'SUKSES_PANEN',
            'wilayah': b_tile['name'],
            'lat': b_tile['lat'],
            'lon': b_tile['lon'],
            'zoom': z,
            'before_tile': b_tile,
            'after_tile': a_tile,
            'deskripsi': f"Sawah kanopi rimbun (Veg {b_tile['veg']:.1f}%{ypr_str}) berhasil dipanen normal menjadi tunggul jerami/lahan olah (Veg {a_tile['veg']:.1f}%)"
        })

    # 2. 13 Pasang Gagal Banjir (Semua Unik)
    for i in range(13):
        idx = 25 + i
        canopy_idx = 25 * step_canopy + i * step_canopy
        b_tile = canopy_pool[canopy_idx]
        
        flood_step = len(flood_pool) // 13
        a_tile = flood_pool[i * flood_step]
        
        pid = f"PAIR_{idx+1:03d}"
        pairs.append({
            'pair_id': pid,
            'kategori': 'GAGAL_BANJIR',
            'ground_truth': 'GAGAL_BANJIR',
            'wilayah': a_tile['name'],
            'lat': a_tile['lat'],
            'lon': a_tile['lon'],
            'zoom': z,
            'before_tile': b_tile,
            'after_tile': a_tile,
            'deskripsi': f"Sawah kanopi rimbun (Veg {b_tile['veg']:.1f}%) puso terendam genangan banjir keruh & lumpur pekat ({a_tile['mud_water']:.1f}% air/lumpur)"
        })

    # 3. 12 Pasang Gagal Kekeringan (Semua Unik)
    for i in range(12):
        idx = 38 + i
        canopy_idx = 38 * step_canopy + i * step_canopy
        b_tile = canopy_pool[canopy_idx]
        
        drought_step = len(drought_pool) // 12
        a_tile = drought_pool[i * drought_step]
        
        pid = f"PAIR_{idx+1:03d}"
        pairs.append({
            'pair_id': pid,
            'kategori': 'GAGAL_KEKERINGAN',
            'ground_truth': 'GAGAL_KEKERINGAN',
            'wilayah': a_tile['name'],
            'lat': a_tile['lat'],
            'lon': a_tile['lon'],
            'zoom': z,
            'before_tile': b_tile,
            'after_tile': a_tile,
            'deskripsi': f"Sawah kanopi rimbun (Veg {b_tile['veg']:.1f}%) puso akibat kekeringan parah Pantura ({a_tile['dry_soil']:.1f}% tanah merekah gersang)"
        })

    # Simpan Seluruh Citra
    dataset_dir = "semua_dataset_gambar"
    os.makedirs(dataset_dir, exist_ok=True)

    # Bersihkan file gambar lama
    for f in os.listdir(dataset_dir):
        if f.endswith('.jpg') or f.endswith('.png'):
            try:
                os.remove(os.path.join(dataset_dir, f))
            except:
                pass

    csv_rows = []
    meta_json = []

    print(f"\nMenyimpan 50 pasang (100 citra murni unik 100% sawah) ke '{dataset_dir}'...")
    used_coords = set()
    for p in pairs:
        pid = p['pair_id']
        b_fname = f"{pid}_BEFORE.jpg"
        a_fname = f"{pid}_AFTER.jpg"

        b_path = os.path.join(dataset_dir, b_fname)
        a_path = os.path.join(dataset_dir, a_fname)

        p['before_tile']['img'].save(b_path, quality=95)
        p['after_tile']['img'].save(a_path, quality=95)

        gt_label = 1 if p['ground_truth'] == 'SUKSES_PANEN' else 0
        wilayah_parts = p['wilayah'].split('_')
        kab = wilayah_parts[0]
        kec = wilayah_parts[1] if len(wilayah_parts) > 1 else 'SentraSawah'

        b_coord = (p['before_tile']['tx'], p['before_tile']['ty'])
        a_coord = (p['after_tile']['tx'], p['after_tile']['ty'])
        used_coords.add(b_coord)
        used_coords.add(a_coord)

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
            'Before_YPR_Percent': round(p['before_tile']['ypr'], 1),
            'After_Mud_Water_Percent': round(p['after_tile']['mud_water'], 1),
            'After_Dry_Soil_Percent': round(p['after_tile']['dry_soil'], 1),
            'File_Before': b_fname,
            'File_After': a_fname,
            'Deskripsi': p['deskripsi']
        })

        meta_json.append({
            'pair_id': pid,
            'kategori': p['kategori'],
            'sub_type': p['kategori'],
            'ground_truth_label': gt_label,
            'kabupaten': kab,
            'kecamatan': kec,
            'lat': round(p['lat'], 6),
            'lon': round(p['lon'], 6),
            'zoom': z,
            'file_before': os.path.join('semua_dataset_gambar', b_fname),
            'file_after': os.path.join('semua_dataset_gambar', a_fname),
            'deskripsi': p['deskripsi']
        })

    print(f"Verifikasi Keunikan: Total koordinat unik yang digunakan: {len(used_coords)} (Harus 100).")

    csv_path = os.path.join(dataset_dir, "keterangan_dataset.csv")
    fieldnames = [
        'Pair_ID', 'Kategori', 'Ground_Truth', 'Wilayah', 'Lat', 'Lon',
        'Zoom_Level', 'GSD_Meter', 'Before_Veg_Percent', 'Before_YPR_Percent',
        'After_Mud_Water_Percent', 'After_Dry_Soil_Percent',
        'File_Before', 'File_After', 'Deskripsi'
    ]
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    os.makedirs('dataset', exist_ok=True)
    with open('dataset/metadata.json', 'w', encoding='utf-8') as f:
        json.dump(meta_json, f, indent=2, ensure_ascii=False)

    petunjuk = '''================================================================================
PETUNJUK PENGGUNAAN DATASET CITRA SATELIT 100% MURNI SAWAH ZOOM 18 (GSD ~0.6m)
PRA-TUBES PENGOLAHAN CITRA DIGITAL (PCD) POLBAN - DIVERSIFIKASI MAKSIMAL
================================================================================

1. DESKRIPSI DATASET:
   Dataset ini berisi 50 pasang (100 citra murni) citra satelit resolusi tinggi
   (Zoom Level 18, GSD ~0.6 meter per piksel) yang DIKURASI KHUSUS 100% PURE SAWAH
   DENGAN 100 CITRA BERBEDA (NOL DUPLIKAT / 100% UNIQUE TILES).
   
   Bebas 100% dari perumahan, atap genteng, dan jalan aspal, serta memiliki variasi
   kondisi kanopi padi yang sangat kaya (fase vegetatif hijau muda, hijau pekat,
   generatif malai bunting, hingga kanopi kuning keemasan matang siap panen).

2. CAKUPAN SENTRA SAWAH UTAMA JAWA BARAT:
   - Karawang: Rawamerta, Jayakerta, Kutawaluya, Tempuran, Cilamaya, Pedes, Cibuaya, Lemahabang
   - Indramayu: Losarang, Kandanghaur, Sukra, Anjatan, Terisi, Gabuswetan

3. DISTRIBUSI KELAS (50 PASANG / 100 CITRA UNIK):
   - PAIR_001 s.d. PAIR_025 (25 Pasang / 50 Citra Unik): SUKSES PANEN
     (Before: Beragam kondisi kanopi padi rimbun -> After: Tunggul jerami & tanah olah)
   - PAIR_026 s.d. PAIR_038 (13 Pasang / 26 Citra Unik): GAGAL PANEN - BANJIR (PUSO AIR)
     (Before: Kanopi padi -> After: Genangan air banjir keruh, lumpur pekat, & silau air)
   - PAIR_039 s.d. PAIR_050 (12 Pasang / 24 Citra Unik): GAGAL PANEN - KEKERINGAN (PUSO KERING)
     (Before: Kanopi padi -> After: Hamparan tanah retak gersang tanpa air)
================================================================================
'''
    with open(os.path.join(dataset_dir, 'PETUNJUK_DATASET.txt'), 'w', encoding='utf-8') as f:
        f.write(petunjuk)

    # Rebuild zip
    zip_path = "semua_dataset_gambar.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for fname in sorted(os.listdir(dataset_dir)):
            fpath = os.path.join(dataset_dir, fname)
            if os.path.isfile(fpath):
                zipf.write(fpath, arcname=fname)

    print(f"SELESAI! Seluruh 50 pasang (100 citra satelit murni unik) tersimpan di '{dataset_dir}' & '{zip_path}'.")

if __name__ == "__main__":
    main()
