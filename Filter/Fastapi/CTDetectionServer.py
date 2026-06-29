"""FastAPI microservice for CT metal artifact detection.

Endpoints:
- GET /api/ct-artifact/health: check service, model, and storage status.
- POST /api/ct-artifact/detect: upload .nii/.nii.gz CT and generate structured outputs.
- GET /api/ct-artifact/results/{request_id}: download result.json.
- GET /api/ct-artifact/files/{request_id}/{file_name}: download masks and previews.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import threading
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import AsyncIterator, Optional

try:
    import SimpleITK as sitk
    from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    from starlette.concurrency import run_in_threadpool
except ImportError as exc:  # pragma: no cover - dependency guard.
    raise SystemExit(
        "Missing service dependencies. Install them with: "
        "pip install -r Filter/Fastapi/requirements.txt"
    ) from exc


if getattr(sys, "frozen", False):
    SERVICE_DIR = Path(sys.executable).resolve().parent
    ASSET_DIR = Path(getattr(sys, "_MEIPASS", SERVICE_DIR))
    MODEL_DIR = ASSET_DIR / "model"
    FRONTEND_DIR = ASSET_DIR / "frontend"
else:
    SERVICE_DIR = Path(__file__).resolve().parent
    FILTER_DIR = SERVICE_DIR.parent
    MODEL_DIR = FILTER_DIR / "model"
    FRONTEND_DIR = SERVICE_DIR / "frontend"
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))
if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))

from config import DEFAULT_OVERLAP, DEFAULT_PATCH_SIZE, DEFAULT_THRESHOLD  # noqa: E402
from Detection.CTArtifactInfer import CTArtifactInfer  # noqa: E402
from ct_artifact_contract import (  # noqa: E402
    API_PREFIX,
    ApiErrorCode,
    api_error,
    build_detection_result,
    find_file_by_name,
    http_exception_handler,
    resolve_output_file,
)
from task_store import (  # noqa: E402
    create_task_record,
    mark_task_failed,
    mark_task_running,
    mark_task_success,
    read_task_record,
)


DEFAULT_WEIGHT_PATH = MODEL_DIR / "runs" / "metal_unet3d" / "best_unet3d_metal.pt"
UPLOAD_DIR = Path(os.getenv("CT_UPLOAD_DIR", SERVICE_DIR / "uploads"))
DEFAULT_OUTPUT_ROOT = (SERVICE_DIR if getattr(sys, "frozen", False) else FILTER_DIR) / "filter_outputs"
OUTPUT_ROOT = Path(os.getenv("CT_OUTPUT_ROOT", os.getenv("CT_RESULT_DIR", DEFAULT_OUTPUT_ROOT)))
LEGACY_RESULT_DIR = SERVICE_DIR / "results"
MODEL_WEIGHT_PATH = Path(os.getenv("CT_MODEL_WEIGHT_PATH", DEFAULT_WEIGHT_PATH))
DEVICE = os.getenv("CT_SERVER_DEVICE") or None
BACKEND = "unet3d"
MODEL_NAME = os.getenv("CT_MODEL_NAME", "metal_unet3d")
MODEL_VERSION = os.getenv("CT_MODEL_VERSION", "v1.0.0")
CHECKPOINT_PROVENANCE = os.getenv("CT_CHECKPOINT_PROVENANCE", "unspecified")
CHECKPOINT_FALLBACK_USED = os.getenv("CT_CHECKPOINT_FALLBACK_USED", "false").lower() == "true"
MATURE_CANDIDATE_PATH = os.getenv("CT_MATURE_CANDIDATE_PATH", "")
MATURE_MAR_CHECKPOINT_PATH = os.getenv("CT_MATURE_MAR_CHECKPOINT_PATH", "")
MATURE_MAR_MODEL_NAME = os.getenv("CT_MATURE_MAR_MODEL_NAME", "")
MATURE_MAR_TASK_TYPE = os.getenv("CT_MATURE_MAR_TASK_TYPE", "")


def parse_patch_size(text: Optional[str]) -> tuple[int, int, int]:
    if not text:
        return DEFAULT_PATCH_SIZE
    parts = [int(part.strip()) for part in text.lower().replace("x", ",").split(",") if part.strip()]
    if len(parts) != 3 or any(part <= 0 for part in parts):
        raise ValueError("CT_SERVER_PATCH_SIZE must look like 32,128,128")
    return tuple(parts)  # type: ignore[return-value]


PATCH_SIZE = parse_patch_size(os.getenv("CT_SERVER_PATCH_SIZE"))
OVERLAP = float(os.getenv("CT_SERVER_OVERLAP", str(DEFAULT_OVERLAP)))
THRESHOLD = float(os.getenv("CT_SERVER_THRESHOLD", str(DEFAULT_THRESHOLD)))


@dataclass
class ModelState:
    available: bool = False
    weight_path: str = str(MODEL_WEIGHT_PATH)
    device: Optional[str] = DEVICE
    error: Optional[str] = None
    checkpoint_provenance: str = CHECKPOINT_PROVENANCE
    checkpoint_fallback_used: bool = CHECKPOINT_FALLBACK_USED
    mature_candidate_path: Optional[str] = MATURE_CANDIDATE_PATH or None
    mature_candidate_exists: bool = bool(MATURE_CANDIDATE_PATH and Path(MATURE_CANDIDATE_PATH).exists())
    mature_mar_checkpoint_path: Optional[str] = MATURE_MAR_CHECKPOINT_PATH or None
    mature_mar_checkpoint_exists: bool = bool(MATURE_MAR_CHECKPOINT_PATH and Path(MATURE_MAR_CHECKPOINT_PATH).exists())
    mature_mar_model_name: Optional[str] = MATURE_MAR_MODEL_NAME or None
    mature_mar_task_type: Optional[str] = MATURE_MAR_TASK_TYPE or None


infer: Optional[CTArtifactInfer] = None
model_state = ModelState()
infer_lock = threading.Lock()


def ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def is_nifti_file(filename: str) -> bool:
    return filename.lower().endswith((".nii", ".nii.gz"))


def strip_nifti_suffix(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".nii.gz"):
        return filename[:-7]
    if lower.endswith(".nii"):
        return filename[:-4]
    return Path(filename).stem


def safe_original_name(filename: Optional[str]) -> str:
    name = Path(filename or "ct.nii.gz").name
    suffix = ".nii.gz" if name.lower().endswith(".nii.gz") else Path(name).suffix
    stem = strip_nifti_suffix(name)
    safe_stem = re.sub(r"[^0-9A-Za-z._-]+", "_", stem).strip("._-") or "ct"
    return f"{safe_stem}{suffix}"


def resolve_legacy_mask_file(mask_filename: str) -> Path:
    try:
        return find_file_by_name(OUTPUT_ROOT, mask_filename)
    except HTTPException:
        pass
    name = Path(mask_filename).name
    if name != mask_filename or not is_nifti_file(name):
        raise api_error(400, ApiErrorCode.INVALID_RESULT_FILE, "非法结果文件名")
    path = (LEGACY_RESULT_DIR / name).resolve()
    root = LEGACY_RESULT_DIR.resolve()
    if root not in path.parents or not path.exists():
        raise api_error(404, ApiErrorCode.RESULT_NOT_FOUND, "掩码文件不存在")
    return path


def task_input_name(filename: str) -> str:
    return "input.nii.gz" if filename.lower().endswith(".nii.gz") else "input.nii"


def load_model_once() -> None:
    global infer, model_state
    if infer is not None:
        return
    try:
        infer = CTArtifactInfer(
            model_weight_path=MODEL_WEIGHT_PATH,
            device=DEVICE,
            patch_size=PATCH_SIZE,
            overlap=OVERLAP,
            threshold=THRESHOLD,
        )
        model_state = ModelState(
            available=True,
            weight_path=str(MODEL_WEIGHT_PATH),
            device=str(infer.device),
            error=None,
            checkpoint_provenance=CHECKPOINT_PROVENANCE,
            checkpoint_fallback_used=CHECKPOINT_FALLBACK_USED,
            mature_candidate_path=MATURE_CANDIDATE_PATH or None,
            mature_candidate_exists=bool(MATURE_CANDIDATE_PATH and Path(MATURE_CANDIDATE_PATH).exists()),
            mature_mar_checkpoint_path=MATURE_MAR_CHECKPOINT_PATH or None,
            mature_mar_checkpoint_exists=bool(MATURE_MAR_CHECKPOINT_PATH and Path(MATURE_MAR_CHECKPOINT_PATH).exists()),
            mature_mar_model_name=MATURE_MAR_MODEL_NAME or None,
            mature_mar_task_type=MATURE_MAR_TASK_TYPE or None,
        )
        print(f"Model loaded: {MODEL_WEIGHT_PATH}")
    except Exception as exc:  # Keep service alive so /health explains the issue.
        infer = None
        model_state = ModelState(
            available=False,
            weight_path=str(MODEL_WEIGHT_PATH),
            device=DEVICE,
            error=str(exc),
            checkpoint_provenance=CHECKPOINT_PROVENANCE,
            checkpoint_fallback_used=CHECKPOINT_FALLBACK_USED,
            mature_candidate_path=MATURE_CANDIDATE_PATH or None,
            mature_candidate_exists=bool(MATURE_CANDIDATE_PATH and Path(MATURE_CANDIDATE_PATH).exists()),
            mature_mar_checkpoint_path=MATURE_MAR_CHECKPOINT_PATH or None,
            mature_mar_checkpoint_exists=bool(MATURE_MAR_CHECKPOINT_PATH and Path(MATURE_MAR_CHECKPOINT_PATH).exists()),
            mature_mar_model_name=MATURE_MAR_MODEL_NAME or None,
            mature_mar_task_type=MATURE_MAR_TASK_TYPE or None,
        )
        print(f"Model load failed: {exc}")


def run_inference(sitk_ct, mask_path: Path):
    if infer is None:
        raise RuntimeError(f"模型不可用: {model_state.error}")
    with infer_lock:
        return infer.predict_from_sitk(sitk_ct, save_mask_path=mask_path)


def build_artifact_reduction_status() -> dict:
    checkpoint_exists = bool(MATURE_MAR_CHECKPOINT_PATH and Path(MATURE_MAR_CHECKPOINT_PATH).exists())
    if not MATURE_MAR_CHECKPOINT_PATH:
        return {
            "enabled": False,
            "registered": False,
            "executable": False,
            "model_name": None,
            "task_type": None,
            "checkpoint_path": None,
            "checkpoint_exists": False,
            "correction_status": "not_configured",
            "corrected_ct_file": None,
            "corrected_ct_url": None,
            "use_for_lesion_input": False,
            "execution_blockers": [],
            "warning": "未配置金属伪影校正模型，本次病灶识别使用原始 CT。",
        }
    if checkpoint_exists:
        return {
            "enabled": False,
            "registered": True,
            "executable": False,
            "model_name": MATURE_MAR_MODEL_NAME or "InDuDoNet",
            "task_type": MATURE_MAR_TASK_TYPE or "metal_artifact_reduction",
            "checkpoint_path": str(Path(MATURE_MAR_CHECKPOINT_PATH).resolve()),
            "checkpoint_exists": True,
            "correction_status": "checkpoint_registered_not_executable",
            "corrected_ct_file": None,
            "corrected_ct_url": None,
            "use_for_lesion_input": False,
            "execution_blockers": [
                "缺少 InDuDoNet 官方 network/indudonet.py 可执行源码。",
                "缺少 ODL/Astra 投影/反投影几何算子运行环境。",
                "业务上传 NIfTI 未提供 InDuDoNet 所需 ma_sinogram、LI_sinogram、metal_trace、LI_CT 等输入。",
            ],
            "warning": "已登记 InDuDoNet 成熟 MAR checkpoint，但当前服务尚未接入其可执行网络与投影域预处理，本次病灶识别仍使用原始 CT。",
        }
    return {
        "enabled": False,
        "registered": False,
        "executable": False,
        "model_name": MATURE_MAR_MODEL_NAME or "InDuDoNet",
        "task_type": MATURE_MAR_TASK_TYPE or "metal_artifact_reduction",
        "checkpoint_path": MATURE_MAR_CHECKPOINT_PATH,
        "checkpoint_exists": False,
        "correction_status": "failed",
        "corrected_ct_file": None,
        "corrected_ct_url": None,
        "use_for_lesion_input": False,
        "execution_blockers": ["配置了 InDuDoNet checkpoint 路径，但文件不存在。"],
        "warning": "配置了金属伪影校正模型路径，但 checkpoint 文件不存在，本次病灶识别使用原始 CT。",
    }


def process_saved_ct_file(
    *,
    request_id: str,
    input_path: Path,
    output_dir: Path,
    original_filename: str,
    content_type: Optional[str],
) -> dict:
    if infer is None:
        raise RuntimeError(f"模型不可用: {model_state.error}")
    output_dir.mkdir(parents=True, exist_ok=True)
    mask_path = output_dir / "mask.nii.gz"
    started = time.perf_counter()
    sitk_ct = sitk.ReadImage(str(input_path))
    sitk_mask = run_inference(sitk_ct, mask_path)
    mask_array = sitk.GetArrayFromImage(sitk_mask)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return build_detection_result(
        request_id=request_id,
        task_id=request_id,
        backend=BACKEND,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        model_weight_path=MODEL_WEIGHT_PATH,
        threshold=THRESHOLD,
        elapsed_ms=elapsed_ms,
        original_file=original_filename,
        upload_path=input_path,
        output_dir=output_dir,
        sitk_ct=sitk_ct,
        sitk_mask=sitk_mask,
        mask_array=mask_array,
        extra_input_metadata={"content_type": content_type},
        artifact_reduction=build_artifact_reduction_status(),
    )


def run_task_inference(task_id: str, input_path: Path, output_dir: Path, original_filename: str, content_type: Optional[str]) -> None:
    started = time.perf_counter()
    try:
        mark_task_running(OUTPUT_ROOT, task_id)
        result = process_saved_ct_file(
            request_id=task_id,
            input_path=input_path,
            output_dir=output_dir,
            original_filename=original_filename,
            content_type=content_type,
        )
        mark_task_success(
            output_root=OUTPUT_ROOT,
            task_id=task_id,
            elapsed_ms=int(result.get("elapsed_ms", 0)),
            preview_urls=result.get("preview_urls", {}),
        )
    except Exception as exc:
        mark_task_failed(
            output_root=OUTPUT_ROOT,
            task_id=task_id,
            error_code=ApiErrorCode.INFERENCE_FAILED,
            error_message=str(exc),
            elapsed_ms=int((time.perf_counter() - started) * 1000),
        )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    ensure_dirs()
    load_model_once()
    yield


app = FastAPI(title="CT金属伪影检测AI服务", version="2.0", lifespan=lifespan)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "CT金属伪影检测服务运行中",
        "docs": "/docs",
        "predict": f"{API_PREFIX}/detect",
        "health": f"{API_PREFIX}/health",
        "ui": "/ui",
        "legacy_predict": "/predict-ct-artifact",
        "legacy_health": "/health",
    }


@app.get("/ui")
async def ui():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="前端文件不存在")
    return FileResponse(index_path)


def health_payload() -> dict:
    return {
        "status": "ok" if model_state.available else "degraded",
        "model": asdict(model_state),
        "module": "ct_artifact_filter",
        "backend": BACKEND,
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "storage": {
            "uploads": str(UPLOAD_DIR.resolve()),
            "outputs": str(OUTPUT_ROOT.resolve()),
            "uploads_exists": UPLOAD_DIR.exists(),
            "outputs_exists": OUTPUT_ROOT.exists(),
        },
        "inference": {
            "patch_size": PATCH_SIZE,
            "overlap": OVERLAP,
            "threshold": THRESHOLD,
        },
    }


@app.get("/health")
@app.get(f"{API_PREFIX}/health")
async def health():
    return health_payload()


async def detect_ct_artifact(file: UploadFile) -> dict:
    if not is_nifti_file(file.filename or ""):
        raise api_error(400, ApiErrorCode.INVALID_FILE_TYPE, "只支持 .nii 或 .nii.gz 格式的 CT 文件")
    if infer is None:
        raise api_error(503, ApiErrorCode.MODEL_UNAVAILABLE, f"模型不可用: {model_state.error}")

    ensure_dirs()
    original_filename = safe_original_name(file.filename)
    unique_id = uuid.uuid4().hex
    upload_path = UPLOAD_DIR / f"{unique_id}_{original_filename}"
    output_dir = OUTPUT_ROOT / unique_id
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with upload_path.open("wb") as dst:
            shutil.copyfileobj(file.file, dst)

        return await run_in_threadpool(
            process_saved_ct_file,
            request_id=unique_id,
            input_path=upload_path,
            output_dir=output_dir,
            original_filename=original_filename,
            content_type=file.content_type,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise api_error(500, ApiErrorCode.INFERENCE_FAILED, f"服务处理失败: {exc}") from exc
    finally:
        try:
            await file.close()
        except Exception:
            pass


@app.post("/predict-ct-artifact")
@app.post(f"{API_PREFIX}/detect")
async def predict_ct_artifact(file: UploadFile = File(...)):
    return await detect_ct_artifact(file)


@app.post(f"{API_PREFIX}/tasks")
async def create_ct_artifact_task(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not is_nifti_file(file.filename or ""):
        raise api_error(400, ApiErrorCode.INVALID_FILE_TYPE, "只支持 .nii 或 .nii.gz 格式的 CT 文件")
    if infer is None:
        raise api_error(503, ApiErrorCode.MODEL_UNAVAILABLE, f"模型不可用: {model_state.error}")

    ensure_dirs()
    task_id = uuid.uuid4().hex
    original_filename = safe_original_name(file.filename)
    output_dir = OUTPUT_ROOT / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    input_path = output_dir / task_input_name(original_filename)

    try:
        with input_path.open("wb") as dst:
            shutil.copyfileobj(file.file, dst)
        task = create_task_record(
            output_root=OUTPUT_ROOT,
            task_id=task_id,
            backend=BACKEND,
            model_name=MODEL_NAME,
            model_version=MODEL_VERSION,
            original_file=original_filename,
            input_file=input_path.name,
        )
        background_tasks.add_task(run_task_inference, task_id, input_path, output_dir, original_filename, file.content_type)
        return task
    finally:
        try:
            await file.close()
        except Exception:
            pass


@app.get(f"{API_PREFIX}/tasks/{{task_id}}")
async def get_ct_artifact_task(task_id: str):
    return read_task_record(OUTPUT_ROOT, task_id)


@app.get(f"{API_PREFIX}/results/{{request_id}}")
async def get_result(request_id: str):
    path = resolve_output_file(OUTPUT_ROOT, request_id, "result.json")
    return FileResponse(path, media_type="application/json", filename=path.name)


@app.get(f"{API_PREFIX}/files/{{request_id}}/{{file_name}}")
async def download_output_file(request_id: str, file_name: str):
    path = resolve_output_file(OUTPUT_ROOT, request_id, file_name)
    media_type = "image/png" if path.suffix.lower() == ".png" else "application/octet-stream"
    if path.name == "result.json":
        media_type = "application/json"
    return FileResponse(path=path, media_type=media_type, filename=path.name)


@app.get(f"{API_PREFIX}/files/{{file_name}}")
async def download_output_file_by_name(file_name: str):
    path = find_file_by_name(OUTPUT_ROOT, file_name)
    return FileResponse(path=path, media_type="application/octet-stream", filename=path.name)


@app.get("/results/{mask_filename}")
async def download_mask(mask_filename: str):
    mask_path = resolve_legacy_mask_file(mask_filename)
    return FileResponse(
        path=mask_path,
        media_type="application/octet-stream",
        filename=mask_path.name,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("CTDetectionServer:app", host="0.0.0.0", port=8000, reload=False)
