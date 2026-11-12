import cv2
import numpy as np
import math

class PCDPipeline:
    # Konstanta Standar Spasial Satelit Zoom 18 & Agronomi BPS Pantura Jabar
    PLOT_AREA_HA = 2.36  # Luas 1 tile satelit Zoom 18 (256x256 px * (0.6m)^2 = 23,593 m2 = 2.36 ha)
    BPS_PRODUCTIVITY_KG_HA = 6000.0  # Rata-rata produktivitas padi sawah irigasi Karawang-Indramayu: 6,0 ton/ha
    TRUCK_CAPACITY_KG = 6000.0  # Daya angkut truk Colt Diesel pedesaan: 6 ton (6.000 kg)
    SACK_CAPACITY_KG = 60.0  # Bobot rata-rata 1 karung gabah basah: 60 kg

    def __init__(self):
        # Morphological kernels
        self.kernel_3x3 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))

    def calculate_yield_and_logistics(self, fvc, ypr, pred_class):
        """
        Formula Konversi Deterministik PCD:
        Mengonversi Kepadatan Kanopi (FVC) menjadi Luas Panen Bersih,
        Estimasi Hasil Produksi Gabah (Kg/Ton), serta Alokasi Truk (< 24 Jam).
        """
        if pred_class == "SUKSES_PANEN":
            net_area_ha = round(float(fvc) * self.PLOT_AREA_HA, 3)
            yield_kg = int(round(net_area_ha * self.BPS_PRODUCTIVITY_KG_HA))
            yield_ton = round(yield_kg / 1000.0, 2)
            sacks_count = int(math.ceil(yield_kg / self.SACK_CAPACITY_KG))
            trucks_count = int(math.ceil(yield_kg / self.TRUCK_CAPACITY_KG))
            action_desc = f"SIAP JEMPUT: {trucks_count} Truk Colt Diesel ke Dryer (< 24 Jam)"
        else:
            net_area_ha = 0.0
            yield_kg = 0
            yield_ton = 0.0
            sacks_count = 0
            trucks_count = 0
            action_desc = "PUSO / BATALKAN TRUK: Terbitkan Tiket Klaim Asuransi AUTP"

        return {
            "net_area_ha": net_area_ha,
            "yield_kg": yield_kg,
            "yield_ton": yield_ton,
            "sacks_count": sacks_count,
            "trucks_count": trucks_count,
            "action_desc": action_desc
        }

    # ==========================================
    # METODE B: METODE USULAN KITA (PROPOSED)
    # (HSV + CLAHE pada Kanal V + Soil-Water Masking)
    # ==========================================
    def preprocess_proposed(self, bgr_img):
        """
        1. Konversi BGR -> HSV
        2. Terapkan CLAHE HANYA pada kanal V (terang-gelap)
           agar pigmen warna asli di kanal H dan S tidak rusak.
        """
        hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        v_clahe = self.clahe.apply(v)
        hsv_norm = cv2.merge([h, s, v_clahe])
        return hsv_norm

    def create_soil_water_mask(self, hsv_norm, v_raw=None, s_raw=None):
        """
        Menyaring piksel untuk mengambil MURNI tajuk tanaman padi
        dan membuang lumpur basah, air banjir, serta silau air:
        1. Buang silau air: S < 35 dan V > 215
        2. Buang air keruh & lumpur basah gelap: V_raw <= 65
        3. Isolasi tanaman padi: Kuning Emas (H >= 18) hingga Hijau Segar (H <= 85)
           dengan saturasi pigmen cukup (S >= 35, V >= 45)
        4. Operasi Morfologi Opening (bersihkan noise) & Closing (tutup lubang daun)
        """
        h, s, v = cv2.split(hsv_norm)
        if v_raw is None:
            v_raw = v
        if s_raw is None:
            s_raw = s

        # Masking tanaman padi aktif (Kuning Emas sampai Hijau Segar, skala satelit Zoom 18)
        crop_mask = ((h >= 18) & (h <= 85) & (s >= 35) & (v >= 45)).astype(np.uint8) * 255

        # Masking genangan air / banjir masif (reflektansi fisik riil v_raw <= 65 atau silau air)
        water_mask = ((v_raw <= 65) | ((s_raw < 35) & (v_raw > 215))).astype(np.uint8) * 255

        # Masking tanah kering merekah / puso kekeringan (reflektansi fisik riil s_raw <= 45 & v_raw in [60, 220])
        dry_soil_mask = ((s_raw <= 45) & (v_raw >= 60) & (v_raw <= 220)).astype(np.uint8) * 255

        # Rapikan crop mask dengan morfologi
        crop_mask = cv2.morphologyEx(crop_mask, cv2.MORPH_OPEN, self.kernel_3x3)
        crop_mask = cv2.morphologyEx(crop_mask, cv2.MORPH_CLOSE, self.kernel_3x3)

        return crop_mask, water_mask, dry_soil_mask

    def extract_features_proposed(self, bgr_img):
        hsv_raw = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
        h_raw, s_raw, v_raw = cv2.split(hsv_raw)
        
        # CLAHE pada kanal V untuk normalisasi kontras tajuk tanaman terhadap bayangan
        v_clahe = self.clahe.apply(v_raw)
        hsv_norm = cv2.merge([h_raw, s_raw, v_clahe])

        crop_mask, water_mask, dry_soil_mask = self.create_soil_water_mask(hsv_norm, v_raw, s_raw)
        total_pixels = bgr_img.shape[0] * bgr_img.shape[1]

        # 1. FVC (Fractional Vegetation Cover)
        crop_pixel_count = np.count_nonzero(crop_mask)
        fvc = crop_pixel_count / total_pixels

        # 2. YPR (Yellow Pixel Ratio - Persentase padi menguning matang: Hue 18-38)
        h, s, v = cv2.split(hsv_norm)
        if crop_pixel_count > 0:
            yellow_pixels = np.count_nonzero((crop_mask > 0) & (h >= 18) & (h <= 38))
            ypr = yellow_pixels / crop_pixel_count
            mean_hue = np.mean(h[crop_mask > 0])
        else:
            ypr = 0.0
            mean_hue = 0.0

        # 3. Water & Dry Soil Ratio
        water_ratio = np.count_nonzero(water_mask) / total_pixels
        dry_soil_ratio = np.count_nonzero(dry_soil_mask) / total_pixels

        # 4. TGI (Triangular Greenness Index)
        b, g, r = cv2.split(bgr_img.astype(np.float32))
        tgi = g - 0.39 * r - 0.61 * b
        mean_tgi = np.mean(tgi[crop_mask > 0]) if crop_pixel_count > 0 else 0.0

        return {
            "fvc": fvc,
            "ypr": ypr,
            "mean_hue": mean_hue,
            "water_ratio": water_ratio,
            "dry_soil_ratio": dry_soil_ratio,
            "mean_tgi": mean_tgi,
            "crop_mask": crop_mask,
            "water_mask": water_mask,
            "dry_soil_mask": dry_soil_mask
        }

    def predict_proposed(self, bgr_before, bgr_after):
        """
        Klasifikasi menggunakan Pohon Keputusan PCD Murni:
        - Membandingkan selisih temporal (Before vs After)
        """
        feat_before = self.extract_features_proposed(bgr_before)
        feat_after = self.extract_features_proposed(bgr_after)

        delta_fvc = feat_before["fvc"] - feat_after["fvc"]

        # Deteksi Kasus
        # A. Kasus Gagal Banjir: Lahan terendam air keruh masif di After (>= 65% area)
        if feat_after["water_ratio"] >= 0.65:
            pred_class = "GAGAL_BANJIR"
            is_success = 0
            reason = f"Terdeteksi genangan air keruh banjir masif ({feat_after['water_ratio']*100:.1f}% area)"
        # B. Kasus Gagal Kekeringan: Lahan merekah kering masif (>= 72%) dengan ketiadaan air (<= 15%)
        elif feat_after["dry_soil_ratio"] >= 0.72 and feat_after["water_ratio"] <= 0.15:
            pred_class = "GAGAL_KEKERINGAN"
            is_success = 0
            reason = f"Terdeteksi tanah kering merekah puso ({feat_after['dry_soil_ratio']*100:.1f}% area)"
        # C. Kasus Sukses Panen: Padi lebat sebelum panen (FVC >= 0.40) dan tajuk berkurang rapi setelah dipotong (delta >= 0.25)
        elif feat_before["fvc"] >= 0.40 and delta_fvc >= 0.25:
            pred_class = "SUKSES_PANEN"
            is_success = 1
            reason = f"Panen berhasil: tajuk padi matang terpotong rapi (penurunan FVC: {delta_fvc*100:.1f}%)"
        elif delta_fvc >= 0.20 and feat_after["fvc"] <= 0.25:
            pred_class = "SUKSES_PANEN"
            is_success = 1
            reason = "Panen normal: area tanaman bersih terpanen menyisakan jerami/tanah olah"
        else:
            # Default fallback jika perubahan tidak mencukupi panen normal
            pred_class = "GAGAL_PANEN"
            is_success = 0
            reason = "Tidak terdeteksi pola panen normal"

        yield_info = self.calculate_yield_and_logistics(feat_before["fvc"], feat_before["ypr"], pred_class)

        return {
            "prediction": pred_class,
            "is_success": is_success,
            "reason": reason,
            "feat_before": feat_before,
            "feat_after": feat_after,
            "delta_fvc": delta_fvc,
            "yield_info": yield_info
        }

    # ==========================================
    # METODE A: BASELINE PAPER BELLIS (LAMA)
    # (Tanpa Masking Lumpur/Air + Rumus ExG = 2G - R - B)
    # ==========================================
    def predict_baseline_paper(self, bgr_before, bgr_after):
        """
        Metode Konvensional / Paper Bellis:
        1. Tidak melakukan CLAHE atau normalisasi HSV.
        2. Menggunakan rumus ExG = 2G - R - B pada seluruh piksel langsung.
        3. Menghitung rata-rata global termasuk lumpur dan genangan air.
        """
        def calc_exg(bgr):
            b = bgr[:, :, 0].astype(np.float32)
            g = bgr[:, :, 1].astype(np.float32)
            r = bgr[:, :, 2].astype(np.float32)
            # Rumus ExG klasik
            exg = 2.0 * g - r - b
            # Masking ExG konvensional: ExG > 0 dianggap tanaman
            plant_mask = (exg > 0).astype(np.uint8) * 255
            ratio = np.count_nonzero(plant_mask) / (bgr.shape[0] * bgr.shape[1])
            return ratio, np.mean(exg), plant_mask

        ratio_before, mean_exg_before, mask_before = calc_exg(bgr_before)
        ratio_after, mean_exg_after, mask_after = calc_exg(bgr_after)

        delta_ratio = ratio_before - ratio_after

        # Kelemahan Fatal ExG:
        # Padi kuning matang memiliki nilai R tinggi sehingga ExG anjlok ke <= 0!
        # Akibatnya ratio_before padi kuning terbaca sangat rendah (< 0.20),
        # sehingga algoritma konvensional mengira sawah kuning sebagai 'tanah' dan gagal mendeteksi panen.
        if ratio_before < 0.25 and ratio_after < 0.25:
            # Salah tebak: mengira sawah tidak pernah ada tanaman karena warna kuning diabaikan ExG
            pred_class = "GAGAL_PANEN"
            is_success = 0
            reason = "ExG gagal: Nilai ExG padi kuning < 0, dikira tanah kosong sejak awal"
        elif delta_ratio > 0.35:
            pred_class = "SUKSES_PANEN"
            is_success = 1
            reason = "Deteksi berbasis penurunan ExG konvensional"
        else:
            pred_class = "GAGAL_PANEN"
            is_success = 0
            reason = "Penurunan ExG tidak signifikan"

        return {
            "prediction": pred_class,
            "is_success": is_success,
            "reason": reason,
            "ratio_before": ratio_before,
            "ratio_after": ratio_after,
            "mask_before": mask_before,
            "mask_after": mask_after
        }
