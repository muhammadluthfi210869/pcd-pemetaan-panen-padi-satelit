import os
import json
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pcd_pipeline import PCDPipeline

def main():
    out_dir = os.path.join("results", "detail_pemrosesan_50_pasang")
    os.makedirs(out_dir, exist_ok=True)
    pipeline = PCDPipeline()

    meta_path = os.path.join("dataset", "metadata.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"Menghasilkan kartu visual hasil pemrosesan lengkap untuk {len(dataset)} pasang citra...")

    for i, item in enumerate(dataset):
        pid = item["pair_id"]
        img_b = cv2.imread(item["file_before"])
        img_a = cv2.imread(item["file_after"])

        res_prop = pipeline.predict_proposed(img_b, img_a)
        res_base = pipeline.predict_baseline_paper(img_b, img_a)

        rgb_b = cv2.cvtColor(img_b, cv2.COLOR_BGR2RGB)
        rgb_a = cv2.cvtColor(img_a, cv2.COLOR_BGR2RGB)

        fig, axs = plt.subplots(2, 3, figsize=(14, 8.5))
        fig.suptitle(
            f"{pid} ({item['kategori']}) - {item['kabupaten']} Kec. {item['kecamatan']} [Lat: {item['lat']}, Lon: {item['lon']}]",
            fontsize=13,
            fontweight="bold",
            color="#1A1A1A",
        )

        # 1. Before RGB
        axs[0, 0].imshow(rgb_b)
        axs[0, 0].set_title("1. Citra Asli BEFORE (T1)", fontsize=10, fontweight="bold")
        axs[0, 0].axis("off")

        # 2. After RGB
        axs[0, 1].imshow(rgb_a)
        axs[0, 1].set_title("2. Citra Asli AFTER (T2)", fontsize=10, fontweight="bold")
        axs[0, 1].axis("off")

        # 3. Crop Mask Before
        axs[0, 2].imshow(res_prop["feat_before"]["crop_mask"], cmap="gray")
        axs[0, 2].set_title(
            f"3. Mask Tajuk Padi Before\nFVC: {res_prop['feat_before']['fvc']*100:.1f}%, YPR: {res_prop['feat_before']['ypr']*100:.1f}%",
            fontsize=10,
            fontweight="bold",
        )
        axs[0, 2].axis("off")

        # 4. Crop Mask After
        axs[1, 0].imshow(res_prop["feat_after"]["crop_mask"], cmap="gray")
        axs[1, 0].set_title(
            f"4. Mask Tajuk Padi After\nFVC: {res_prop['feat_after']['fvc']*100:.1f}% (ΔFVC: {res_prop['delta_fvc']*100:.1f}%)",
            fontsize=10,
            fontweight="bold",
        )
        axs[1, 0].axis("off")

        # 5. Mask Air & Lumpur / Tanah Kering After
        if "BANJIR" in item["kategori"]:
            mask_anomali = res_prop["feat_after"]["water_mask"]
            title_anomali = f"5. Mask Air/Lumpur (After)\nWater Ratio: {res_prop['feat_after']['water_ratio']*100:.1f}%"
        else:
            mask_anomali = res_prop["feat_after"]["dry_soil_mask"]
            title_anomali = f"5. Mask Tanah Kering (After)\nDry Soil: {res_prop['feat_after']['dry_soil_ratio']*100:.1f}%"

        axs[1, 1].imshow(mask_anomali, cmap="gray")
        axs[1, 1].set_title(title_anomali, fontsize=10, fontweight="bold")
        axs[1, 1].axis("off")

        # 6. Status Keputusan & Alokasi Logistik Gabah (< 24 Jam)
        gt_name = "SUKSES_PANEN" if item["ground_truth_label"] == 1 else item["sub_type"]
        status_prop = "BENAR (100%)" if res_prop["is_success"] == item["ground_truth_label"] else "SALAH"
        status_base = "BENAR" if res_base["is_success"] == item["ground_truth_label"] else "SALAH"
        yi = res_prop["yield_info"]

        if item["ground_truth_label"] == 1:
            prod_info = (
                f"• ESTIMASI PRODUKSI & LOGISTIK:\n"
                f"  Luas Panen : {yi['net_area_ha']:.2f} ha (FVC: {res_prop['feat_before']['fvc']*100:.1f}%)\n"
                f"  Est. Gabah : {yi['yield_kg']:,} kg ({yi['yield_ton']} ton)\n"
                f"  Karung 60kg: {yi['sacks_count']} karung\n"
                f"  Kebutuhan  : {yi['trucks_count']} Truk Colt Diesel\n"
                f"  Urgensi    : Jemput < 24 Jam ke Dryer"
            )
        else:
            prod_info = (
                f"• ESTIMASI PRODUKSI & LOGISTIK:\n"
                f"  Luas Panen : 0.00 ha (Puso Bencana)\n"
                f"  Est. Gabah : 0 kg (Gagal Panen)\n"
                f"  Truk Logis.: 0 unit (BATALKAN TRUK)\n"
                f"  Tindakan   : Tiket Asuransi Tani (AUTP)"
            )

        status_box = (
            f"KEPUTUSAN DETEKSI SISTEM:\n"
            f"─────────────────────────────\n"
            f"• Ground Truth : {gt_name}\n"
            f"• Prediksi PCD : {res_prop['prediction']} [{status_prop}]\n"
            f"• Baseline ExG : {res_base['prediction']} [{status_base}]\n\n"
            f"{prod_info}"
        )
        axs[1, 2].text(
            0.05,
            0.92,
            status_box,
            transform=axs[1, 2].transAxes,
            fontsize=9.5,
            verticalalignment="top",
            bbox=dict(boxstyle="square,pad=0.6", facecolor="#F8F9FA", edgecolor="#333333", linewidth=1.1),
            fontfamily="monospace",
        )
        axs[1, 2].axis("off")

        plt.tight_layout(rect=[0, 0, 1, 0.94])
        save_path = os.path.join(out_dir, f"{pid}_detail_pemrosesan.png")
        plt.savefig(save_path, dpi=140)
        plt.close()

    print(f"SELESAI! Seluruh 50 kartu detail pemrosesan tersimpan di '{out_dir}'.")

if __name__ == "__main__":
    main()
