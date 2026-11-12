# Pemetaan Kesiapan Panen Padi dan Deteksi Anomali Gagal Panen dari Citra Satelit Resolusi Tinggi Multi-Temporal (Zoom 18) melalui Normalisasi Iluminasi HSV dan Soil-Water Masking

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8.svg)](https://opencv.org/)
[![Status](https://img.shields.io/badge/Status-Completed%20%26%20Published-success.svg)](#)

Repositori ini memuat implementasi lengkap naskah paper ilmiah, pipeline algoritma, dataset satelit resolusi tinggi murni, hasil evaluasi studi ablasi, serta aplikasi web interaktif untuk penelitian:
**"Pemetaan Kesiapan Panen Padi dan Deteksi Anomali Gagal Panen dari Citra Satelit Resolusi Tinggi Multi-Temporal (Zoom 18) melalui Normalisasi Iluminasi HSV dan Soil-Water Masking"**.

---

## 🌾 1. Latar Belakang & Urgensi Ilmiah

* **Krisis Pascapanen (*Food Loss*)**: Kehilangan hasil panen padi nasional di Indonesia mencapai **9,8% hingga 10,2%** (BRIN & Bappenas, 2021). Salah satu penyebab utamanya adalah keterlambatan penjemputan gabah basah melebihi **batas kritis biologis 24 jam** setelah pemotongan, yang memicu fermentasi spontan, pemanasan di dalam karung, butir kuning (*yellowing*), dan kebusukan.
* **Cacat Fatal Indeks Konvensional (*Excess Green / ExG*)**:
  Literatur pertanian klasik sering mengandalkan rumus $\text{ExG} = 2G - R - B$ (Woebbecke et al., 1995). Rumus ini dirancang hanya untuk daun hijau ($G \gg R, B$). Namun, saat padi matang siap dipanen, konsentrasi klorofil menyusut dan digantikan karotenoid sehingga tajuk berwarna **kuning keemasan** ($R \ge G$). Akibatnya, nilai ExG anjlok drastis ke $\le 0$, sehingga padi siap panen **terhapus dan dikira tanah kosong** (*False Negative* masif).
* **Distorsi Spektral Lumpur & Silau Air (*Sun-Glint*)**:
  Pada persawahan tropis basah, air keruh berlumut dan lumpur bajakan memiliki nilai $G$ sedikit lebih tinggi dari $R$ dan $B$, memicu *False Positive* fatal di mana air banjir dan lumpur dikira vegetasi hijau aktif.

---

## 💡 2. Arsitektur Metode Usulan (PCD Murni Deterministik)

Tanpa menggunakan model *Deep Learning* yang membutuhkan pelatihan komputasi berjam-jam (seperti 2D/3D-CNN pada Bellis et al., 2022), sistem ini menerapkan operasi matriks piksel deterministik murni:

1. **Normalisasi Iluminasi Bayangan Awan (HSV + CLAHE)**:
   Konversi RGB ke HSV, lalu terapkan *Contrast Limited Adaptive Histogram Equalization* (CLAHE) **hanya pada kanal V (terang-gelap)** agar bayangan awan lokal dinetralkan tanpa mendistorsi pigmen warna asli pada kanal H dan S.
2. **Soil and Water Masking Berbasis Fisik Permukaan**:
   * **Eliminasi Lumpur & Air Gelap**: Intensitas kecerahan fisik rendah ($V_{\text{raw}} \le 65$).
   * **Eliminasi Silau Surya (*Sun-Glint*)**: Saturasi sangat rendah dan nilai sangat tinggi ($S < 35$ dan $V > 215$).
   * **Isolasi Kanopi Padi Aktif**: Rentang Hue tanaman padi ($18 \le H \le 85$), saturasi alami ($S \ge 35$), dan kecerahan kanopi ($V \ge 45$), dilanjutkan operasi morfologi matematika *Opening* dan *Closing* $3 \times 3$.
3. **Pohon Keputusan Dua Fase (*Dual-Stage Decision Tree*)**:
   * **Fase 1 Pre-Harvest ($T_1$)**: Evaluasi kematangan kanopi ($\text{FVC} \ge 40\%$ dan $\text{YPR} \ge 40\%$) untuk peringatan armada truk (< 24 jam).
   * **Fase 2 Post-Harvest Validation ($T_2$)**: Validasi keberhasilan panen normal ($\Delta\text{FVC} \ge 25\%$) vs anomali bencana puso banjir ($\text{Water Ratio} \ge 65\%$) vs puso kekeringan Pantura ($\text{Dry Soil Ratio} \ge 72\%$).
4. **Formulasi Estimasi Tonase & Logistik Truk (< 24 Jam)**:
   * Luas Petak Sub-Blok Satelit Zoom 18: $256 \times 256\text{ px} \times (0,6\text{ m})^2 = \mathbf{2,36\text{ ha}}$.
   * Luas Bersih Tanaman: $A_{\text{eff}} = 2,36\text{ ha} \times \text{FVC}$.
   * Estimasi Produksi: $\text{Yield (kg)} = A_{\text{eff}} \times 6.000\text{ kg/ha}$ (Tolok ukur resmi BPS Karawang/Indramayu).
   * Alokasi Armada: $N_{\text{truk}} = \lceil \text{Yield} / 6.000\text{ kg} \rceil$ (Truk Colt Diesel 6 ton).

---

## 📊 3. Hasil Evaluasi Kuantitatif & Studi Ablasi (50 Pasang / 100 Citra Unik)

Diuji pada 50 pasang citra satelit resolusi tinggi murni 100% sawah (Zoom Level 18, GSD ~0,6 m/piksel) langsung dari satelit Google Earth/Maxar di sentra lumbung padi Jawa Barat (**Kabupaten Karawang** dan **Kabupaten Indramayu**) tanpa penambahan noise sintetis maupun area pemukiman warga:

| Metrik Evaluasi | Baseline Konvensional (Bellis et al. / ExG) | Metode Usulan (HSV + Masking) | Peningkatan (Gap) |
| :--- | :---: | :---: | :---: |
| **Akurasi Global** | 32,00% | **100,00%** | **+68,00% (Sempurna)** |
| **Recall (Sensitivitas Panen)** | 20,00% | **100,00%** | **+80,00% (25/25 Terdeteksi)** |
| **Presisi** | 26,32% | **100,00%** | **+73,68% (Bebas False Alarm)** |
| **F1-Score Harmonik** | 22,73% | **100,00%** | **+77,27%** |
| **True Positive (TP)** | 5 petak | **25 petak** | **+20 petak** |
| **True Negative (TN)** | 11 petak | **25 petak** | **+14 petak** |
| **False Positive (FP)** | 14 petak (Fatal Banjir) | **0 petak (Nol Kesalahan)** | **-14 petak tuntas** |
| **False Negative (FN)** | 20 petak (Padi Kuning) | **0 petak (Nol Kesalahan)** | **-20 petak tuntas** |
| **Waktu Komputasi** | 5 – 18 jam (Training HPC) | **< 15 ms (Zero-Training Laptop)** | **Instan / Real-Time** |

---

## 📁 4. Struktur Direktori Repositori

```
├── dataset/
│   └── metadata.json                   # Metadata terstruktur 50 pasang titik koordinat, kecamatan & ground-truth
├── results/
│   ├── ablation_metrics_chart.png      # Grafik batang perbandingan metrik kinerja kuantitatif
│   ├── diagram_workflow_sistem.png     # Diagram alur kerja (workflow) akademik monokrom
│   ├── pembuktian_masking_lumpur_air.png # Bukti eliminasi lumpur, air & isolasi tajuk padi
│   ├── pembuktian_zoom_lumpur_silau.png  # Mikro zoom-in dan kurva distribusi intensitas kanal V
│   ├── sample_sukses_panen.png         # Bukti visual spasial kasus sukses panen raya
│   ├── sample_gagal_banjir.png         # Bukti visual spasial kasus gagal panen puso banjir
│   ├── sample_gagal_kekeringan.png     # Bukti visual spasial kasus gagal panen puso kekeringan
│   ├── metrics_report.json             # Laporan lengkap seluruh metrik evaluasi kuantitatif
│   ├── viewer_inspeksi_50_pasang.html  # Dashboard web inspeksi interaktif 50 pasang hasil pemrosesan
│   └── detail_pemrosesan_50_pasang/    # Kartu gambar 6-panel pemrosesan lengkap PAIR_001 s.d. PAIR_050
├── semua_dataset_gambar/
│   ├── PAIR_001_BEFORE.jpg ...         # 100 file citra satelit resolusi tinggi murni Zoom 18
│   ├── keterangan_dataset.csv          # Tabel metadata lengkap (koordinat, tonase, luas, truk)
│   └── PETUNJUK_DATASET.txt            # Petunjuk penggunaan dataset
├── src/
│   ├── pcd_pipeline.py                 # Pipeline inti algoritma PCD (HSV CLAHE, Masking, Decision Tree, Yield)
│   ├── evaluate_ablation.py            # Script komparasi metrik uji ablasi 50 pasang
│   ├── build_full_publication_paper.py # Generator dokumen paper Word formal standar IEEE/Springer
│   ├── curate_pure_sawah_only.py       # Algoritma seleksi murni sawah bebas pemukiman (Harris + Color)
│   └── generate_all_50_process_cards.py# Generator kartu diagnostik 6-panel 50 pasang
├── static/ & templates/                # Frontend dashboard interaktif web
├── main.py                             # Server backend FastAPI untuk demo web interaktif
├── Paper_Ilmiah_PCD_Final_Publikasi.docx # Naskah paper Word publikasi ilmiah final
├── PAPER_ILMIAH_PCD_LENGKAP.md         # Naskah lengkap paper ilmiah dalam format Markdown
├── Skrip_Presentasi_PraTUBES_PCD_Jelas_dan_Detail.docx # Naskah skrip presentasi & tanya-jawab dosen
├── fpls-13-716506.pdf                  # Paper acuan Bellis et al. (2022) Frontiers in Plant Science
├── semua_dataset_gambar.zip            # Arsip zip 100 citra satelit & metadata
└── README.md
```

---

## 🚀 5. Cara Menjalankan Aplikasi & Evaluasi

### Prasyarat
Pastikan Python 3.10+ telah terinstal beserta pustaka pendukung:
```bash
pip install opencv-python numpy matplotlib pillow fastapi uvicorn python-docx
```

### Opsi A: Menjalankan Dashboard Web Interaktif
Cukup jalankan file `run.bat` (Windows) atau jalankan perintah:
```bash
uvicorn main:app --reload --port 8000
```
Buka peramban (*browser*) pada alamat:
👉 **http://127.0.0.1:8000**

### Opsi B: Membuka Galeri Web Inspeksi 50 Pasang Pemrosesan
Buka file HTML lokal langsung di peramban Chrome/Edge:
👉 `results/viewer_inspeksi_50_pasang.html`  
Fitur yang tersedia:
* Filter kategori: *Semua (50)*, *Sukses Panen (25)*, *Gagal Banjir (13)*, dan *Gagal Kekeringan (12)*.
* Ringkasan otomatis: Kepadatan Kanopi (FVC), Padi Kuning (YPR), Luas Panen Efektif (ha), Estimasi Gabah (kg/ton), dan Kebutuhan Truk Colt Diesel.
* Klik gambar mana pun untuk memperbesar dalam resolusi tinggi.

### Opsi C: Menjalankan Uji Evaluasi & Studi Ablasi
```bash
python src/evaluate_ablation.py
```

---

## 👥 Tim Peneliti
* **Program Studi**: D4 Teknik Informatika, Jurusan Teknik Komputer dan Informatika
* **Institusi**: Politeknik Negeri Bandung (POLBAN), Bandung, Indonesia
* **Mata Kuliah**: Pengolahan Citra Digital (PCD) — Semester 5
