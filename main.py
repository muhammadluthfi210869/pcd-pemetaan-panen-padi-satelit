import os
import sys
import json
import base64
import io
import cv2
import numpy as np

# Tambahkan src ke path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "src"))

from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pcd_pipeline import PCDPipeline

app = FastAPI(
    title="PCD Satelit Padi Jawa Barat - POLBAN",
    description="Aplikasi Pemetaan Kesiapan Panen & Deteksi Sukses/Gagal Panen dari Citra Satelit"
)

# Mount direktori static, dataset, results, dan semua_dataset_gambar
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/dataset", StaticFiles(directory=os.path.join(BASE_DIR, "dataset")), name="dataset")
app.mount("/results", StaticFiles(directory=os.path.join(BASE_DIR, "results")), name="results")
app.mount("/semua_dataset_gambar", StaticFiles(directory=os.path.join(BASE_DIR, "semua_dataset_gambar")), name="semua_dataset_gambar")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
pipeline = PCDPipeline()

# Cache direktori untuk menyimpan visualisasi mask sementara
CACHE_DIR = os.path.join(BASE_DIR, "static", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def mat_to_base64(img_mat, is_mask=False):
    if is_mask:
        # Beri colormap agar menarik di web (misal Greens untuk padi, Hot untuk lumpur)
        success, encoded = cv2.imencode(".png", img_mat)
    else:
        success, encoded = cv2.imencode(".png", img_mat)
    if success:
        return "data:image/png;base64," + base64.b64encode(encoded.tobytes()).decode("utf-8")
    return ""

def load_metadata():
    meta_path = os.path.join(BASE_DIR, "dataset", "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def load_metrics():
    met_path = os.path.join(BASE_DIR, "results", "metrics_report.json")
    if os.path.exists(met_path):
        with open(met_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    metadata = load_metadata()
    metrics = load_metrics()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "dataset": metadata,
            "metrics": metrics,
            "total_samples": len(metadata)
        }
    )

@app.get("/api/analyze/{pair_id}")
async def analyze_pair(pair_id: str):
    metadata = load_metadata()
    item = next((x for x in metadata if x["pair_id"] == pair_id), None)
    if not item:
        return JSONResponse({"status": "error", "message": "Pair ID tidak ditemukan"}, status_code=404)

    path_before = os.path.join(BASE_DIR, item["file_before"])
    path_after = os.path.join(BASE_DIR, item["file_after"])

    bgr_before = cv2.imread(path_before)
    bgr_after = cv2.imread(path_after)

    # 1. Jalankan Metode Usulan Kita (HSV + CLAHE + Masking)
    res_prop = pipeline.predict_proposed(bgr_before, bgr_after)
    # 2. Jalankan Metode Baseline Paper (ExG Tanpa Masking)
    res_base = pipeline.predict_baseline_paper(bgr_before, bgr_after)

    # Generate base64 masks
    mask_before_b64 = mat_to_base64(res_prop["feat_before"]["crop_mask"], is_mask=True)
    mask_after_b64 = mat_to_base64(res_prop["feat_after"]["crop_mask"], is_mask=True)
    water_mask_b64 = mat_to_base64(res_prop["feat_after"]["water_mask"], is_mask=True)
    dry_mask_b64 = mat_to_base64(res_prop["feat_after"]["dry_soil_mask"], is_mask=True)
    base_mask_b64 = mat_to_base64(res_base["mask_before"], is_mask=True)

    fb = res_prop["feat_before"]
    fa = res_prop["feat_after"]

    return JSONResponse({
        "status": "success",
        "pair_id": pair_id,
        "kabupaten": item["kabupaten"],
        "kecamatan": item["kecamatan"],
        "sub_type": item["sub_type"],
        "deskripsi": item["deskripsi"],
        "ground_truth_label": item["ground_truth_label"],
        "ground_truth_text": "SUKSES PANEN" if item["ground_truth_label"] == 1 else "GAGAL PANEN",
        "url_before": "/" + item["file_before"].replace("\\", "/"),
        "url_after": "/" + item["file_after"].replace("\\", "/"),
        "proposed": {
            "prediction": res_prop["prediction"],
            "is_success": res_prop["is_success"],
            "is_correct": res_prop["is_success"] == item["ground_truth_label"],
            "reason": res_prop["reason"],
            "fvc_before": round(fb["fvc"] * 100, 1),
            "fvc_after": round(fa["fvc"] * 100, 1),
            "delta_fvc": round(res_prop["delta_fvc"] * 100, 1),
            "ypr_before": round(fb["ypr"] * 100, 1),
            "water_ratio_after": round(fa["water_ratio"] * 100, 1),
            "dry_soil_ratio_after": round(fa["dry_soil_ratio"] * 100, 1),
            "mask_crop_before": mask_before_b64,
            "mask_crop_after": mask_after_b64,
            "mask_water_after": water_mask_b64,
            "mask_dry_after": dry_mask_b64
        },
        "baseline": {
            "prediction": res_base["prediction"],
            "is_success": res_base["is_success"],
            "is_correct": res_base["is_success"] == item["ground_truth_label"],
            "reason": res_base["reason"],
            "ratio_before": round(res_base["ratio_before"] * 100, 1),
            "ratio_after": round(res_base["ratio_after"] * 100, 1),
            "mask_before": base_mask_b64
        }
    })

@app.post("/api/upload_analyze")
async def upload_analyze(file_before: UploadFile = File(...), file_after: UploadFile = File(...)):
    contents_b = await file_before.read()
    contents_a = await file_after.read()

    np_b = np.frombuffer(contents_b, np.uint8)
    np_a = np.frombuffer(contents_a, np.uint8)

    bgr_before = cv2.imdecode(np_b, cv2.IMREAD_COLOR)
    bgr_after = cv2.imdecode(np_a, cv2.IMREAD_COLOR)

    if bgr_before is None or bgr_after is None:
        return JSONResponse({"status": "error", "message": "Gagal membaca format citra"}, status_code=400)

    # Resize to standardized 256x256 if needed
    bgr_before = cv2.resize(bgr_before, (256, 256))
    bgr_after = cv2.resize(bgr_after, (256, 256))

    res_prop = pipeline.predict_proposed(bgr_before, bgr_after)
    res_base = pipeline.predict_baseline_paper(bgr_before, bgr_after)

    url_b_b64 = mat_to_base64(bgr_before)
    url_a_b64 = mat_to_base64(bgr_after)
    mask_b_b64 = mat_to_base64(res_prop["feat_before"]["crop_mask"], is_mask=True)
    mask_a_b64 = mat_to_base64(res_prop["feat_after"]["crop_mask"], is_mask=True)
    water_b64 = mat_to_base64(res_prop["feat_after"]["water_mask"], is_mask=True)
    dry_b64 = mat_to_base64(res_prop["feat_after"]["dry_soil_mask"], is_mask=True)
    base_mask_b64 = mat_to_base64(res_base["mask_before"], is_mask=True)

    fb = res_prop["feat_before"]
    fa = res_prop["feat_after"]

    return JSONResponse({
        "status": "success",
        "pair_id": "custom_upload",
        "kabupaten": "User Custom Upload",
        "kecamatan": "Lahan Uji Mandiri",
        "sub_type": "custom",
        "deskripsi": "Citra diunggah langsung oleh pengguna",
        "ground_truth_label": -1,
        "ground_truth_text": "Custom",
        "url_before": url_b_b64,
        "url_after": url_a_b64,
        "proposed": {
            "prediction": res_prop["prediction"],
            "is_success": res_prop["is_success"],
            "is_correct": True,
            "reason": res_prop["reason"],
            "fvc_before": round(fb["fvc"] * 100, 1),
            "fvc_after": round(fa["fvc"] * 100, 1),
            "delta_fvc": round(res_prop["delta_fvc"] * 100, 1),
            "ypr_before": round(fb["ypr"] * 100, 1),
            "water_ratio_after": round(fa["water_ratio"] * 100, 1),
            "dry_soil_ratio_after": round(fa["dry_soil_ratio"] * 100, 1),
            "mask_crop_before": mask_b_b64,
            "mask_crop_after": mask_a_b64,
            "mask_water_after": water_b64,
            "mask_dry_after": dry_b64
        },
        "baseline": {
            "prediction": res_base["prediction"],
            "is_success": res_base["is_success"],
            "is_correct": True,
            "reason": res_base["reason"],
            "ratio_before": round(res_base["ratio_before"] * 100, 1),
            "ratio_after": round(res_base["ratio_after"] * 100, 1),
            "mask_before": base_mask_b64
        }
    })

if __name__ == "__main__":
    import uvicorn
    print("Menjalankan PCD Satelit Web App di http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
