import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pcd_pipeline import PCDPipeline

os.makedirs('results', exist_ok=True)
pipeline = PCDPipeline()

# Gunakan citra murni satelit Zoom 18:
# PAIR_001_BEFORE (Karawang Cibuaya) & PAIR_026_AFTER (Karawang Rawamerta Flooded Mud)
bgr_veg = cv2.imread('semua_dataset_gambar/PAIR_001_BEFORE.jpg')
bgr_flood = cv2.imread('semua_dataset_gambar/PAIR_026_AFTER.jpg')
rgb_veg = cv2.cvtColor(bgr_veg, cv2.COLOR_BGR2RGB)
rgb_flood = cv2.cvtColor(bgr_flood, cv2.COLOR_BGR2RGB)

hsv_veg = cv2.cvtColor(bgr_veg, cv2.COLOR_BGR2HSV)
hsv_flood = cv2.cvtColor(bgr_flood, cv2.COLOR_BGR2HSV)

# ==============================================================================
# GAMBAR 1: PEMBUKTIAN ZOOM-IN MIKRO & KURVA DISTRIBUSI INTENSITAS V (MONOCHROME/SLATE)
# ==============================================================================
fig, axes = plt.subplots(1, 4, figsize=(18, 4.8))
fig.suptitle("PEMBUKTIAN SPEKTRAL SATELIT MURNI ZOOM 18 (GSD ~0.6m): KONTUR ALAMI TANPA NOISE SINTETIS", 
             fontsize=12.5, fontweight='bold', color='#000000')

# Panel 1: Citra Satelit Utuh
axes[0].imshow(rgb_veg)
axes[0].set_title("1. Citra Satelit Asli Zoom 18\n(Karawang - Sentra Padi)", fontsize=10, fontweight='bold', color='#000000')
cv2.rectangle(rgb_veg, (40, 40), (140, 140), (220, 20, 20), 2)
axes[0].axis('off')

# Panel 2: Mikro Zoom-in Kanopi Rimbun (Crop 100x100)
crop_canopy = cv2.cvtColor(bgr_veg, cv2.COLOR_BGR2RGB)[40:140, 40:140]
axes[1].imshow(crop_canopy)
axes[1].set_title("2. Detail Tajuk Padi Asli\n(Rona Daun Alami, V: 60-180)", fontsize=10, fontweight='bold', color='#000000')
axes[1].axis('off')

# Panel 3: Mikro Zoom-in Lumpur Bajakan & Air Keruh Asli (Crop Flood)
crop_mud = cv2.cvtColor(bgr_flood, cv2.COLOR_BGR2RGB)[60:160, 60:160]
axes[2].imshow(crop_mud)
axes[2].set_title("3. Detail Lumpur & Air Nyata\n(Reflektansi Rendah, V: 15-55)", fontsize=10, fontweight='bold', color='#000000')
axes[2].axis('off')

# Panel 4: Kurva Distribusi Histogram Alami Kanal V (Distribusi Gauss Kontinu)
v_veg = hsv_veg[:, :, 2].flatten()
v_mud = hsv_flood[:, :, 2].flatten()

axes[3].hist(v_mud, bins=40, density=True, alpha=0.60, color='#333333', label='Lumpur & Air Alami (V <= 65)')
axes[3].hist(v_veg, bins=40, density=True, alpha=0.60, color='#888888', label='Kanopi Padi Alami (V > 65)')
axes[3].axvline(x=65, color='#000000', linestyle='--', linewidth=2, label='Ambang Batas PCD (V = 65)')
axes[3].set_title("4. Distribusi Intensitas Kanal V\n(Kurva Kontinu Murni Satelit)", fontsize=10, fontweight='bold', color='#000000')
axes[3].set_xlabel("Nilai Kecerahan Kanal V (0-255)", fontsize=9, fontweight='bold', color='#000000')
axes[3].set_ylabel("Densitas Frekuensi", fontsize=9, fontweight='bold', color='#000000')
axes[3].legend(loc='upper right', fontsize=8.5, framealpha=0.9)
axes[3].grid(True, linestyle=':', alpha=0.5)

plt.tight_layout(rect=[0, 0, 1, 0.90])
p1_path = "results/pembuktian_zoom_lumpur_silau.png"
plt.savefig(p1_path, dpi=250)
plt.close()
print(f"Disimpan: {p1_path}")

# ==============================================================================
# GAMBAR 2: DEKOMPOSISI 4-PANEL SOIL & WATER MASKING (ACADEMIC GRAYSCALE MASKS)
# ==============================================================================
feat_veg = pipeline.extract_features_proposed(bgr_veg)

fig, axes = plt.subplots(1, 4, figsize=(18, 4.8))
fig.suptitle("DEKOMPOSISI SOIL & WATER MASKING PADA SATELIT MURNI ZOOM 18 (GSD ~0.6m)", 
             fontsize=12.5, fontweight='bold', color='#000000')

# Panel 1: RGB
axes[0].imshow(cv2.cvtColor(bgr_veg, cv2.COLOR_BGR2RGB))
axes[0].set_title("1. Citra Input Murni Satelit\n(Komposit Warna Sejati RGB)", fontsize=10, fontweight='bold', color='#000000')
axes[0].axis('off')

# Panel 2: Water & Mud Mask
axes[1].imshow(feat_veg['water_mask'], cmap='gray')
axes[1].set_title(f"2. Masking Air & Lumpur\n(Area Tereliminasi: {feat_veg['water_ratio']*100:.1f}%)", 
                  fontsize=10, fontweight='bold', color='#000000')
axes[1].axis('off')

# Panel 3: Dry Soil Mask
axes[2].imshow(feat_veg['dry_soil_mask'], cmap='gray')
axes[2].set_title(f"3. Masking Tanah Kering/Pematang\n(Area Tereliminasi: {feat_veg['dry_soil_ratio']*100:.1f}%)", 
                  fontsize=10, fontweight='bold', color='#000000')
axes[2].axis('off')

# Panel 4: Murni Tajuk Padi (Crop Mask)
axes[3].imshow(feat_veg['crop_mask'], cmap='gray')
axes[3].set_title(f"4. Murni Tajuk Padi Terisolasi\n(FVC: {feat_veg['fvc']*100:.1f}%, YPR: {feat_veg['ypr']*100:.1f}%)", 
                  fontsize=10, fontweight='bold', color='#000000')
axes[3].axis('off')

plt.tight_layout(rect=[0, 0, 1, 0.90])
p2_path = "results/pembuktian_masking_lumpur_air.png"
plt.savefig(p2_path, dpi=250)
plt.close()
print(f"Disimpan: {p2_path}")
