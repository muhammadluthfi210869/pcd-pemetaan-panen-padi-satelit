import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def create_word_paper():
    doc = Document()
    
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # 1. JUDUL PAPER
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("Pemetaan Kesiapan Panen Padi dan Deteksi Anomali Gagal Panen dari Citra Satelit Multi-Temporal melalui Normalisasi Iluminasi HSV dan Soil-Water Masking\n")
    title_run.font.name = 'Times New Roman'
    title_run.font.size = Pt(16)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(27, 94, 32)

    sub_run = title_p.add_run("Rice Harvest Readiness Mapping and Crop Failure Anomaly Detection from Multi-Temporal Satellite Imagery via HSV Illumination Normalization and Soil-Water Masking")
    sub_run.font.name = 'Times New Roman'
    sub_run.font.size = Pt(12)
    sub_run.font.italic = True
    sub_run.font.color.rgb = RGBColor(85, 85, 85)

    # 2. PENULIS & AFILIASI
    author_p = doc.add_paragraph()
    author_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    author_p.paragraph_format.space_before = Pt(8)
    author_p.paragraph_format.space_after = Pt(14)
    a1 = author_p.add_run("Kelompok Riset Pengolahan Citra Digital\n")
    a1.font.name = 'Times New Roman'
    a1.font.size = Pt(11)
    a1.font.bold = True
    
    a2 = author_p.add_run("Program Studi D4 Teknik Informatika, Jurusan Teknik Komputer dan Informatika\nPoliteknik Negeri Bandung (POLBAN), Bandung, Indonesia\nKontak: pcd.polban@polban.ac.id")
    a2.font.name = 'Times New Roman'
    a2.font.size = Pt(10)
    a2.font.italic = True

    doc.add_paragraph("―" * 48).alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 3. ABSTRAK INDONESIA
    abs_p = doc.add_paragraph()
    abs_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    abs_title = abs_p.add_run("ABSTRAK— ")
    abs_title.font.name = 'Times New Roman'
    abs_title.font.size = Pt(10)
    abs_title.font.bold = True
    
    abs_text = abs_p.add_run(
        "Kehilangan pangan pascapanen (food loss) pada komoditas padi di Indonesia mencapai 9,8% hingga 10,2%, di mana salah satu faktor pemicu utamanya adalah keterlambatan penjemputan gabah basah menuju fasilitas pengering (dryer) melampaui batas kritis biologis 24 jam setelah pemotongan. Pemanfaatan citra penginderaan jauh satelit atau drone optik berbiaya rendah (RGB standard) berpotensi besar memetakan kesiapan panen secara presisi. Namun, pendekatan baseline konvensional seperti pada Bellis et al. (2022) mengandalkan pelatihan Deep Learning 2D/3D-CNN yang membutuhkan komputasi masif di server HPC (5–18 jam) serta menggunakan kalkulasi rata-rata spasial tanpa penyaringan latar belakang, di samping ketergantungan literatur klasik pada indeks Excess Green (ExG = 2G - R - B). Pada kondisi sawah tropis, pendekatan tersebut mengalami kegagalan sistematis: pantulan silau air matahari dan tanah lumpur terbuka mendistorsi nilai rata-rata spektral, sementara rumus ExG keliru mengklasifikasikan padi kuning keemasan siap panen sebagai tanah kosong karena nilai ExG jatuh ke <= 0 akibat tingginya reflektansi kanal Merah (R >= G). Penelitian ini mengusulkan arsitektur Pengolahan Citra Digital (PCD) murni berbasis matriks deterministik tanpa pelatihan model: (1) Normalisasi iluminasi bayangan awan lokal via CLAHE pada kanal V di ruang warna HSV, (2) Soil and Water Masking untuk mengisolasi kanopi murni dari lumpur gelap (V < 60) dan silau air (V > 215, S < 35), serta (3) Kerangka kerja pemantauan dua fase (Dual-Stage Monitoring Framework): evaluasi kesiapan panen dini (T1) dan validasi hasil serta deteksi anomali bencana puso banjir dan kekeringan (T2). Diuji pada benchmark 50 pasang citra satelit multi-temporal (100 citra) di sentra lumbung padi Jawa Barat (Kabupaten Karawang dan Indramayu) dengan simulasi perturbasi lingkungan terkontrol (Controlled Semi-Synthetic Disturbance), metode usulan mencapai akurasi 94,00%, presisi 89,29%, F1-score 94,34%, dan sensitivitas deteksi panen (Recall) sempurna 100,00% (25/25 petak panen terdeteksi). Sebaliknya, metode baseline konvensional hanya memperoleh akurasi 40,00% dan Recall 8,00% (False Negative 92%). Hasil ini membuktikan bahwa pendekatan PCD murni mampu menutup celah bias latar belakang secara instan dalam hitungan milidetik pada laptop standar, memberikan solusi aplikatif bagi manajemen rantai pasok panen padi nasional."
    )
    abs_text.font.name = 'Times New Roman'
    abs_text.font.size = Pt(10)
    abs_text.font.italic = True

    kw_p = doc.add_paragraph()
    kw_p.paragraph_format.space_after = Pt(12)
    kw_label = kw_p.add_run("Kata Kunci: ")
    kw_label.font.name = 'Times New Roman'
    kw_label.font.size = Pt(10)
    kw_label.font.bold = True
    kw_body = kw_p.add_run("Pengolahan Citra Digital, Kesiapan Panen Padi, Satelit Multi-Temporal, Ruang Warna HSV, Soil-Water Masking, Dual-Stage Monitoring, Studi Ablasi, Puso Pertanian.")
    kw_body.font.name = 'Times New Roman'
    kw_body.font.size = Pt(10)

    # 4. ABSTRACT ENGLISH
    abs_en_p = doc.add_paragraph()
    abs_en_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    abs_en_title = abs_en_p.add_run("ABSTRACT— ")
    abs_en_title.font.name = 'Times New Roman'
    abs_en_title.font.size = Pt(10)
    abs_en_title.font.bold = True
    
    abs_en_text = abs_en_p.add_run(
        "Post-harvest food loss in Indonesian rice production accounts for approximately 9.8% to 10.2%, predominantly driven by delays in hauling wet unhusked grain to drying facilities exceeding the critical 24-hour physiological threshold. While low-cost optical RGB satellite or UAV imagery presents substantial potential for harvest readiness mapping, conventional baselines such as Bellis et al. (2022) rely on computationally intensive 2D/3D-CNN architectures requiring hours of HPC training and employ unmasked spatial averages, alongside conventional RGB indices such as Excess Green (ExG = 2G - R - B). In tropical paddy environments, this approach fails systematically: wet mud and specular water reflections heavily corrupt average spectral readings, while the ExG index erroneously classifies golden-yellow ripening rice as bare ground because high Red channel reflectance (R >= G) forces ExG values to drop below zero. This study proposes a deterministic, training-free Digital Image Processing (DIP) pipeline: (1) Local cloud shadow illumination normalization via CLAHE strictly applied to the V channel in HSV color space, (2) Physical Soil and Water Masking isolating genuine rice canopies by discarding dark mud (V < 60) and specular solar glints (V > 215, S < 35), and (3) A Dual-Stage Monitoring Framework: pre-harvest early warning at T1 and multi-temporal post-harvest validation (T2) with rule-based decision trees for crop failure anomaly detection (flood inundation and drought puso). Evaluated on a 50-pair multi-temporal satellite benchmark (100 images) across prime rice-producing regencies of West Java (Karawang and Indramayu) using controlled semi-synthetic environmental disturbance modeling, the proposed pipeline achieves an overall accuracy of 94.00%, precision of 89.29%, F1-score of 94.34%, and a flawless 100.00% Recall (25/25 harvest sites correctly identified). Conversely, the conventional baseline yielded only 40.00% accuracy and 8.00% Recall (92% False Negative rate). These findings demonstrate that pure mathematical DIP operations effectively eliminate environmental background noise within milliseconds on standard hardware, offering a highly practical tool for agricultural supply chain logistics."
    )
    abs_en_text.font.name = 'Times New Roman'
    abs_en_text.font.size = Pt(10)
    abs_en_text.font.italic = True

    kw_en_p = doc.add_paragraph()
    kw_en_p.paragraph_format.space_after = Pt(16)
    kw_en_label = kw_en_p.add_run("Keywords: ")
    kw_en_label.font.name = 'Times New Roman'
    kw_en_label.font.size = Pt(10)
    kw_en_label.font.bold = True
    kw_en_body = kw_en_p.add_run("Digital Image Processing, Rice Harvest Readiness, Multi-Temporal Satellite Imagery, HSV Color Space, Soil-Water Masking, Dual-Stage Monitoring, Ablation Study, Agricultural Crop Failure.")
    kw_en_body.font.name = 'Times New Roman'
    kw_en_body.font.size = Pt(10)

    doc.add_paragraph("―" * 48).alignment = WD_ALIGN_PARAGRAPH.CENTER

    def add_h1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
        r = h.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = RGBColor(27, 94, 32)
        return h

    def add_h2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
        r = h.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11.5)
        r.font.bold = True
        return h

    def add_body(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)
        return p

    def add_figure(img_path, caption):
        if os.path.exists(img_path):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_picture(img_path, width=Inches(6.0))
            cap = doc.add_paragraph()
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap.paragraph_format.space_before = Pt(4)
            cap.paragraph_format.space_after = Pt(10)
            r = cap.add_run(caption)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(9.5)
            r.font.italic = True

    # 1. PENDAHULUAN
    add_h1("1. PENDAHULUAN")
    add_h2("1.1 Latar Belakang & Urgensi Batas Kritis 24 Jam")
    add_body(
        "Padi (Oryza sativa L.) merupakan komoditas pangan paling strategis di Indonesia, dengan Provinsi Jawa Barat—khususnya Kabupaten Karawang dan Indramayu—sebagai salah satu lumbung pangan utama penyangga pasokan beras nasional. Namun demikian, sektor perberasan nasional masih dihadapkan pada ancaman susut pascapanen (post-harvest food loss). Berdasarkan data Kementerian PPN/Bappenas dan Badan Riset dan Inovasi Nasional (BRIN, 2021), persentase kehilangan hasil padi nasional mencapai 9,8% hingga 10,2% dari total produksi tahunan."
    )
    add_body(
        "Salah satu faktor pemicu utama kehilangan hasil ini adalah keterlambatan penjemputan gabah basah setelah pemotongan melebihi batas biologis kritis 24 jam. Pada iklim tropis basah dengan kelembapan udara tinggi, gabah dipanen dengan kadar air basah mencapai 22% hingga 26%. Jika dalam 24 jam gabah menumpuk di pematang sawah akibat keterlambatan armada truk pengangkut menuju fasilitas pengering mekanis (dryer), proses fermentasi alami dan kenaikan suhu spontan di dalam karung akan merusak gabah, memicu butir kuning (yellowing), bau apek, dan busuk. Oleh karena itu, diperlukan pemetaan zonasi kematangan panen dari udara yang cepat dan akurat untuk memprioritaskan jadwal logistik penjemputan gabah."
    )

    add_h2("1.2 Tantangan Optik Penginderaan Jauh pada Lahan Persawahan Tropis")
    add_body(
        "Sensor multispektral atau hiperspektral berbiaya mahal menjadi kendala adopsi operasional berskala luas bagi petani dan penggilingan padi di negara berkembang. Penggunaan citra satelit atau kamera drone optik standar RGB berbiaya rendah adalah alternatif paling masuk akal. Namun, pada skala observasi penginderaan jauh persawahan tropis, pembacaan kanopi tanaman sangat rentan terdistorsi oleh elemen non-vegetasi: (1) area genangan air petak sawah dan saluran irigasi yang memantulkan silau surya (specular solar glint), (2) tanah lumpur basah terbuka dan pematang non-vegetasi yang menyerap cahaya, serta (3) fluktuasi intensitas akibat bayangan awan kumulus lokal."
    )

    add_h2("1.3 Tinjauan Kritis Paper Acuan (Bellis et al., 2022) & Cacat Matematis Excess Green (ExG)")
    add_body(
        "Sebagai rujukan pembanding utama, penelitian ini menelaah secara kritis karya Bellis et al. (2022) di jurnal Frontiers in Plant Science (Q1) berjudul 'Detecting Intra-Field Variation in Rice Yield With Unmanned Aerial Vehicle Imagery and Deep Learning'. Bellis et al. meneliti variasi hasil panen padi seluas 16 hektare di Arkansas, AS, menggunakan citra UAV multispektral dan melatih model Deep Learning 2D/3D-CNN di superkomputer HPC selama 5 hingga 18 jam. Pendekatan tersebut memiliki kelemahan mendasar: sangat berat secara komputasi dan tidak melakukan penyaringan latar belakang tanah/air (unmasked spatial average)."
    )
    add_body(
        "Di sisi lain, indeks vegetasi RGB konvensional yang kerap diadopsi dalam literatur adalah Excess Green (ExG = 2G - R - B; Woebbecke et al., 1995). Secara aljabar piksel, rumus ExG dirancang hanya untuk vegetasi daun hijau muda (G >> R dan G >> B). Pada saat padi memasuki fase siap panen, konsentrasi klorofil menyusut dan digantikan oleh karotenoid, sehingga tajuk padi berubah menjadi KUNING KEEMASAN (R dan G sama-sama tinggi, R >= G). Ketika nilai R meningkat menyamai atau melampaui G, perhitungan rumus ExG langsung anjlok ke <= 0 (nol atau negatif). Akibat fatalnya, algoritma konvensional mengira padi kuning yang paling siap panen sebagai tanah kosong dan menghapusnya dari analisis, menyebabkan False Negative mencapai lebih dari 90%."
    )

    add_h2("1.4 Kerangka Kerja Pemantauan Dua Fase (Dual-Stage Monitoring Framework)")
    add_body(
        "Untuk menyelaraskan antara kebutuhan logistik penjemputan 24 jam dan pelacakan hasil panen multi-temporal, penelitian ini mengusulkan Kerangka Kerja Pemantauan Dua Fase (Dual-Stage Monitoring Framework): (1) Fase 1 Pre-Harvest Early Warning (T1) untuk memetakan kesiapan panen berdasarkan rasio FVC >= 70% dan YPR >= 75% guna memberikan peringatan dini truk penjemputan gabah basah (< 24 jam); dan (2) Fase 2 Multi-Temporal Post-Harvest Validation (T2) untuk memvalidasi keberhasilan pemotongan padi (delta FVC >= 30%) serta mendeteksi anomali bencana puso (luapan banjir atau kekeringan ekstrem)."
    )

    # 2. METODOLOGI PENELITIAN
    add_h1("2. METODOLOGI PENELITIAN")
    add_h2("2.1 Desain Benchmark & Wilayah Kajian Dataset Multi-Temporal")
    add_body(
        "Penelitian difokuskan pada Provinsi Jawa Barat, mencakup dua sentra beras nasional: Kabupaten Karawang dan Kabupaten Indramayu. Kompilasi dataset pengujian dibangun menggunakan metodologi pemodelan perturbasi lingkungan terkontrol (Controlled Semi-Synthetic Disturbance Modeling). Dalam ranah pengolahan citra dan penginderaan jauh, pengujian berbasis injeksi gangguan terkontrol pada citra satelit riil merupakan metodologi ilmiah standar yang diakui guna mengisolasi dan menguji ketahanan matematis algoritma terhadap derau spesifik tanpa terbiaskan oleh variabel atmosferik yang acak."
    )
    add_body(
        "Sebanyak 50 pasangan citra satelit multi-temporal (total 100 citra beresolusi tinggi 256x256 piksel) dibangun dari citra dasar satelit Google Earth / Sentinel-2 pada titik koordinat nyata di Karawang dan Indramayu: (1) 25 pasang kasus Sukses Panen Raya di Kutawaluya, Jayakerta, Rawamerta, Lemahabang, Terisi, dan Sukra; (2) 13 pasang kasus Gagal Panen Akibat Banjir di Cilebar, Cilamaya Kulon, Tempuran, dan Banyusari; serta (3) 12 pasang kasus Gagal Panen Akibat Kekeringan El Nino di Kandanghaur, Losarang, Kroya, dan Patrol."
    )

    add_h2("2.2 Normalisasi Iluminasi Ruang Warna HSV via CLAHE")
    add_body(
        "Format RGB mencampurkan informasi warna asli dan intensitas cahaya matahari. Citra mula-mula dikonversi ke ruang warna HSV (Hue, Saturation, Value). Normalisasi bayangan awan lokal diterapkan dengan Contrast Limited Adaptive Histogram Equalization (CLAHE) HANYA pada kanal V (terang-gelap) dengan clip limit = 2.5 dan tile grid = 8x8. Kanal H (identitas rona) dan S (kejenuhan) tidak disentuh agar pigmen warna asli tanaman padi tetap terjaga."
    )

    add_h2("2.3 Formulasi Fisik Soil and Water Masking")
    add_body(
        "Penyaringan piksel latar belakang dilakukan menggunakan 3 aturan ambang batas fisik di ruang HSV: (1) Masker silau pantulan air matahari: V > 215 dan S < 35; (2) Masker lumpur basah gelap: V < 60; (3) Masker kanopi padi murni: rona kuning hingga hijau (20 <= H <= 85) dengan saturasi pigmen aktif memadai S >= 75 dan V >= 60. Derau spasial dihilangkan menggunakan operasi morfologi biner Opening dan Closing 3x3 piksel."
    )

    add_h2("2.4 Ekstraksi Indeks Fisik & Pohon Keputusan Deterministik")
    add_body(
        "Pada setiap petak dihitung Fractional Vegetation Cover (FVC), Yellow Pixel Ratio (YPR: Hue 18-38), Rasio Air Banjir, dan Rasio Tanah Merekah Puso. Klasifikasi status lahan didasarkan pada pohon keputusan temporal: jika Water Ratio After > 35% maka Gagal Banjir; jika Dry Soil Ratio After >= 78% dan YPR Before <= 5% maka Gagal Kekeringan; jika FVC Before >= 50% dan delta FVC >= 30% maka Sukses Panen."
    )

    # 3. HASIL DAN PEMBAHASAN
    add_h1("3. HASIL DAN PEMBAHASAN")
    add_h2("3.1 Pembuktian Visual & Spektral Soil-Water Masking")
    add_body(
        "Gambar 1 dan Gambar 2 mendokumentasikan investigasi mikro dan tahapan penyaringan Soil-Water Masking pada petak sawah panen raya Kutawaluya, Karawang."
    )
    add_figure("results/pembuktian_zoom_lumpur_silau.png", "Gambar 1. Investigasi mikro zoom-in 4x dan kurva distribusi intensitas kanal V yang membuktikan pemisahan tegas antara lumpur basah (V < 60), kanopi padi (60 <= V <= 215), dan silau air (V > 215).")
    add_figure("results/pembuktian_masking_lumpur_air.png", "Gambar 2. Dekomposisi 4-panel Soil and Water Masking memperlihatkan eliminasi lumpur basah dan pantulan silau air tanpa merusak tajuk padi.")

    add_h2("3.2 Analisis Kuantitatif Komparatif Studi Ablasi (Head-to-Head)")
    add_body(
        "Tabel 1 menyajikan perbandingan metrik kinerja kuantitatif antara metode baseline konvensional versus metode usulan penelitian ini pada 50 dataset satelit riil Jawa Barat."
    )

    table = doc.add_table(rows=9, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    headers = ["Metrik Kinerja", "Baseline Konvensional (ExG)", "Metode Usulan (HSV+Masking)", "Peningkatan (Gap)"]
    row_data = [
        ["Akurasi Global", "40,00%", "94,00%", "+54,00%"],
        ["Recall (Sensitivitas Panen)", "8,00%", "100,00%", "+92,00% (25/25 Terdeteksi)"],
        ["Presisi", "22,22%", "89,29%", "+67,07%"],
        ["F1-Score Harmonik", "11,76%", "94,34%", "+82,58%"],
        ["True Positive (TP)", "2 petak", "25 petak", "+23 petak"],
        ["True Negative (TN)", "18 petak", "22 petak", "+4 petak"],
        ["False Positive (FP)", "7 petak", "3 petak", "-4 petak"],
        ["False Negative (FN)", "23 petak (Fatal)", "0 petak (Nol Kesalahan)", "-23 petak tuntas"]
    ]

    for col_idx, h_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = h_text
        set_cell_background(cell, "1B5E20")
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r.font.size = Pt(10)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)

    for row_idx, r_vals in enumerate(row_data, 1):
        for col_idx, val in enumerate(r_vals):
            cell = table.cell(row_idx, col_idx)
            cell.text = val
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(9.5)
                if col_idx == 2 or col_idx == 3:
                    r.font.bold = True
            if row_idx % 2 == 1:
                set_cell_background(cell, "F1F8E9")

    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    add_figure("results/ablation_metrics_chart.png", "Gambar 3. Grafik batang komparasi metrik evaluasi dan rekapitulasi Confusion Matrix antara metode baseline konvensional versus metode usulan PCD murni.")

    add_h2("3.3 Evaluasi Kasus Bencana Lapangan Ekstrem")
    add_body(
        "Kinerja algoritma pada deteksi anomali bencana puso banjir di Karawang dan kekeringan di Indramayu diperlihatkan pada Gambar 4, Gambar 5, dan Gambar 6."
    )
    add_figure("results/sample_sukses_panen.png", "Gambar 4. Visualisasi komparasi multi-temporal kasus Sukses Panen Raya di Kecamatan Kutawaluya, Karawang.")
    add_figure("results/sample_gagal_banjir.png", "Gambar 5. Visualisasi deteksi bencana gagal panen akibat luapan banjir di Kecamatan Cilebar, Karawang.")
    add_figure("results/sample_gagal_kekeringan.png", "Gambar 6. Visualisasi deteksi bencana gagal panen akibat kekeringan puso di Kecamatan Kandanghaur, Indramayu. Label kesalahan baseline telah dikoreksi sebagai False Positive (FP).")

    add_h2("3.4 Analisis Kompleksitas & Waktu Komputasi")
    add_body(
        "Berbeda dengan model 2D/3D-CNN Bellis et al. yang memerlukan server superkomputer HPC dan waktu training 5–18 jam, algoritma PCD murni usulan ini tidak memerlukan pelatihan data sama sekali (zero training). Waktu inferensi per pasangan citra satelit hanya memakan waktu 40 milidetik pada laptop standar tanpa GPU, dengan kompleksitas waktu asimptotik O(N) yang berbanding lurus secara linier terhadap luas piksel citra."
    )

    # 4. KESIMPULAN
    add_h1("4. KESIMPULAN DAN SARAN")
    add_body(
        "Penelitian ini membuktikan secara ilmiah bahwa pendekatan Pengolahan Citra Digital murni melalui normalisasi HSV (CLAHE pada kanal V) dan Soil-Water Masking berhasil mengatasi kelemahan mendasar literatur konvensional. Pada pengujian 50 pasang dataset satelit multi-temporal Jawa Barat (Karawang dan Indramayu), metode usulan melonjakkan akurasi dari 40,00% menjadi 94,00% (+54,00%) dan menorehkan Recall sempurna 100,00% (+92,00%) dengan waktu eksekusi instan 40 milidetik di laptop standar. Sistem dua fase ini sangat aplikatif untuk memprioritaskan jadwal logistik penjemputan gabah basah guna mencegah food loss dalam batas kritis 24 jam sekaligus memvalidasi keberhasilan panen di lapangan."
    )

    # DAFTAR PUSTAKA
    add_h1("DAFTAR PUSTAKA")
    refs = [
        "Badan Pusat Statistik. (2024). Luas Panen dan Produksi Padi di Indonesia 2023 (Angka Tetap). Badan Pusat Statistik Republik Indonesia, Jakarta.",
        "Bappenas & BRIN. (2021). Laporan Kajian Kehilangan dan Pemborosan Pangan (Food Loss and Waste) di Indonesia dalam Mendukung Ketahanan Pangan Nasional. Kementerian PPN/Bappenas, Jakarta.",
        "Bellis, E. S., Hashem, A. A., & Runkle, B. R. (2022). Detecting intra-field variation in rice yield with unmanned aerial vehicle imagery and deep learning. Frontiers in Plant Science, 13, 716506. https://doi.org/10.3389/fpls.2022.716506",
        "Gitelson, A. A., Kaufman, Y. J., Stark, R., & Rundquist, D. (2002). Novel algorithms for remote estimation of vegetation fraction. Remote Sensing of Environment, 80(1), 76–87.",
        "Gonzalez, R. C., & Woods, R. E. (2018). Digital Image Processing (4th ed.). Pearson Education, New York.",
        "Gummert, M., Hung, N. V., Chivenge, P., & Douthwaite, B. (2020). Sustainable Rice Straw Management. Springer Nature, Cham, Switzerland.",
        "Hunt, E. R., Doraiswamy, P. C., McMurtrey, J. E., Daughtry, C. S., Perry, E. M., & Akhmedov, B. (2013). A visible band index for remote sensing crop chlorophyll content at the canopy scale. International Journal of Applied Earth Observation and Geoinformation, 21, 103–112.",
        "Maimaitijiang, M., Sagan, V., Sidike, P., Hartling, S., Esposito, F., & Fritschi, F. B. (2020). Soybean yield prediction using multi-temporal UAV data and machine learning. ISPRS Journal of Photogrammetry and Remote Sensing, 160, 136–154.",
        "Nugraha, S., Rickman, J. F., & Gummert, M. (2020). Rice postharvest losses in developing countries: Case study of Indonesia. Rice Science, 27(4), 312–325.",
        "Otsu, N. (1979). A threshold selection method from gray-level histograms. IEEE Transactions on Systems, Man, and Cybernetics, 9(1), 62–66.",
        "Wang, F., Yao, X., Zheng, H., Xu, C., & Zhu, Y. (2022). Evaluation of spectral indices for estimating rice ripening stage using top-view UAV RGB imagery. Computers and Electronics in Agriculture, 198, 107085.",
        "Woebbecke, D. M., Meyer, G. E., Von Bargen, K., & Mortensen, D. A. (1995). Color indices for weed identification under various soil, residue, and lighting conditions. Transactions of the ASAE, 38(1), 259–269.",
        "Zuiderveld, K. (1994). Contrast limited adaptive histogram equalization. Graphics Gems IV, Academic Press, San Diego, 474–485."
    ]
    for idx, ref in enumerate(refs, 1):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(f"[{idx}] {ref}")
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10)

    out_docx = "Paper_Ilmiah_PCD_Pemetaan_Panen_Padi_Satelit_Revisi.docx"
    doc.save(out_docx)
    print(f"Paper ilmiah DOCX berhasil diperbarui: {out_docx}")

if __name__ == "__main__":
    create_word_paper()
