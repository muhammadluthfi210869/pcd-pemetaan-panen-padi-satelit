import json, cv2, os
from pcd_pipeline import PCDPipeline

pipeline = PCDPipeline()
with open('dataset/metadata.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

items_js = []
for item in dataset:
    pid = item['pair_id']
    img_b = cv2.imread(item['file_before'])
    img_a = cv2.imread(item['file_after'])
    res_prop = pipeline.predict_proposed(img_b, img_a)
    yi = res_prop['yield_info']
    items_js.append({
        'pid': pid,
        'kat': item['kategori'],
        'kab': item['kabupaten'],
        'kec': item['kecamatan'],
        'lat': item['lat'],
        'lon': item['lon'],
        'fvc': round(res_prop['feat_before']['fvc']*100, 1),
        'ypr': round(res_prop['feat_before']['ypr']*100, 1),
        'delta_fvc': round(res_prop['delta_fvc']*100, 1),
        'net_area_ha': yi['net_area_ha'],
        'yield_kg': yi['yield_kg'],
        'yield_ton': yi['yield_ton'],
        'sacks': yi['sacks_count'],
        'trucks': yi['trucks_count'],
        'action': yi['action_desc']
    })

html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Galeri Inspeksi 50 Pasang Hasil Pemrosesan PCD & Logistik Panen</title>
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f6f8; margin: 0; padding: 25px; color: #222; }}
    h1 {{ text-align: center; margin-bottom: 5px; color: #111; font-size: 24px; }}
    p.sub {{ text-align: center; color: #666; margin-top: 0; margin-bottom: 25px; font-size: 14px; }}
    .filters {{ display: flex; justify-content: center; gap: 12px; margin-bottom: 25px; flex-wrap: wrap; }}
    .btn {{ padding: 8px 18px; border: 1px solid #ccc; background: white; cursor: pointer; border-radius: 20px; font-weight: bold; font-size: 13px; transition: all 0.2s; }}
    .btn:hover, .btn.active {{ background: #1a1a1a; color: white; border-color: #1a1a1a; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(440px, 1fr)); gap: 22px; }}
    .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); overflow: hidden; border: 1px solid #e2e8f0; }}
    .card-header {{ padding: 10px 14px; font-weight: bold; font-size: 13px; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; border-bottom: 1px solid #edf2f7; }}
    .badge {{ padding: 3px 8px; border-radius: 4px; font-size: 11px; text-transform: uppercase; font-weight: bold; }}
    .badge-sukses {{ background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }}
    .badge-banjir {{ background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }}
    .badge-kering {{ background: #fff3e0; color: #e65100; border: 1px solid #ffcc80; }}
    .card img {{ width: 100%; height: auto; display: block; cursor: pointer; transition: transform 0.2s; }}
    .card img:hover {{ transform: scale(1.01); }}
    .card-body {{ padding: 12px 14px; font-size: 12.5px; line-height: 1.5; color: #334155; background: #fff; }}
    .metric-row {{ display: flex; justify-content: space-between; margin-bottom: 4px; border-bottom: 1px dashed #f1f5f9; padding-bottom: 3px; }}
    .metric-label {{ color: #64748b; font-weight: 500; }}
    .metric-value {{ font-weight: bold; color: #0f172a; }}
    .logistics-box {{ margin-top: 8px; padding: 7px 10px; border-radius: 6px; font-size: 11.5px; font-weight: 600; }}
    .logistics-sukses {{ background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; }}
    .logistics-gagal {{ background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; }}
    #modal {{ display: none; position: fixed; z-index: 999; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); justify-content: center; align-items: center; }}
    #modal img {{ max-width: 95%; max-height: 95%; border-radius: 6px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
  </style>
</head>
<body>
  <h1>Galeri Inspeksi 50 Pasang Hasil Pemrosesan PCD & Logistik Panen</h1>
  <p class="sub">Citra Satelit Resolusi Tinggi Zoom 18 (GSD ~0.6m/px) — Kabupaten Karawang & Indramayu</p>

  <div class="filters">
    <button class="btn active" onclick="filterCards('all', this)">Semua (50)</button>
    <button class="btn" onclick="filterCards('SUKSES_PANEN', this)">Sukses Panen (25)</button>
    <button class="btn" onclick="filterCards('GAGAL_BANJIR', this)">Gagal Banjir (13)</button>
    <button class="btn" onclick="filterCards('GAGAL_KEKERINGAN', this)">Gagal Kekeringan (12)</button>
  </div>

  <div class="grid" id="cardGrid"></div>

  <div id="modal" onclick="closeModal()">
    <img id="modalImg" src="" alt="Detail">
  </div>

  <script>
    const dataset = {json.dumps(items_js, ensure_ascii=False)};

    const grid = document.getElementById('cardGrid');
    dataset.forEach(d => {{
      let badgeClass = 'badge-sukses';
      let badgeLabel = 'Sukses Panen';
      let logClass = 'logistics-sukses';
      let logText = `🚚 Kebutuhan: ${{d.trucks}} Truk Colt Diesel (${{d.sacks}} karung) | Jemput < 24 Jam`;

      if (d.kat === 'GAGAL_BANJIR') {{ 
        badgeClass = 'badge-banjir'; 
        badgeLabel = 'Puso Banjir'; 
        logClass = 'logistics-gagal';
        logText = `⚠️ Status Puso Banjir: 0 Truk (Batalkan) | Terbitkan Tiket Klaim AUTP`;
      }} else if (d.kat === 'GAGAL_KEKERINGAN') {{ 
        badgeClass = 'badge-kering'; 
        badgeLabel = 'Puso Kekeringan'; 
        logClass = 'logistics-gagal';
        logText = `⚠️ Status Puso Kering: 0 Truk (Batalkan) | Terbitkan Tiket Klaim AUTP`;
      }}

      const card = document.createElement('div');
      card.className = 'card';
      card.setAttribute('data-kat', d.kat);
      const imgSrc = 'detail_pemrosesan_50_pasang/' + d.pid + '_detail_pemrosesan.png';

      card.innerHTML = `
        <div class="card-header">
          <span>${{d.pid}} (${{d.kab}} - Kec. ${{d.kec}})</span>
          <span class="badge ${{badgeClass}}">${{badgeLabel}}</span>
        </div>
        <img src="${{imgSrc}}" loading="lazy" alt="${{d.pid}}" onclick="openModal('${{imgSrc}}')">
        <div class="card-body">
          <div class="metric-row">
            <span class="metric-label">Kepadatan Kanopi (FVC) / Matang (YPR):</span>
            <span class="metric-value">${{d.fvc}}% / ${{d.ypr}}%</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">Luas Bersih Panen / Total Petak:</span>
            <span class="metric-value">${{d.net_area_ha}} ha / 2.36 ha</span>
          </div>
          <div class="metric-row">
            <span class="metric-label">Estimasi Produksi Gabah (6 ton/ha):</span>
            <span class="metric-value">${{d.yield_kg.toLocaleString()}} kg (${{d.yield_ton}} ton)</span>
          </div>
          <div class="logistics-box ${{logClass}}">
            ${{logText}}
          </div>
        </div>
      `;
      grid.appendChild(card);
    }});

    function filterCards(kat, btn) {{
      document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.card').forEach(c => {{
        if (kat === 'all' || c.getAttribute('data-kat') === kat) {{
          c.style.display = 'block';
        }} else {{
          c.style.display = 'none';
        }}
      }});
    }}

    function openModal(src) {{
      document.getElementById('modalImg').src = src;
      document.getElementById('modal').style.display = 'flex';
    }}
    function closeModal() {{
      document.getElementById('modal').style.display = 'none';
    }}
  </script>
</body>
</html>
"""

with open('results/viewer_inspeksi_50_pasang.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print('Updated results/viewer_inspeksi_50_pasang.html successfully!')
