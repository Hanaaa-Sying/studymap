import json
import os
import shutil
import tempfile
import threading
import uuid
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from fill_mode.framework import generate_framework
from fill_mode.mubu_export import to_mubu_markdown
from fill_mode.parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
)
from review_mode.rhetoric import extract_rhetoric_chunked
from store.schema import RhetoricEntry

app = FastAPI()
DATA_DIR = Path(os.getenv("STUDYMAP_DATA_DIR", "./data"))

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

# in-memory job store: job_id -> {status, result_path, error}
_jobs: dict[str, dict] = {}


def _extract_full(tmp_path: str, suffix: str) -> str:
    if suffix == ".pdf":
        return extract_text_from_pdf(tmp_path)
    return extract_text_from_docx(tmp_path)


def _process_job(
    job_id: str, tmp_path: str, suffix: str, course: str, mode: str,
    lang_mode: str = "original", lang_from: str = "auto", lang_to: str = "zh",
):
    try:
        course_dir = DATA_DIR / course.replace(" ", "_")
        course_dir.mkdir(parents=True, exist_ok=True)

        lang_kwargs = dict(lang_mode=lang_mode, lang_from=lang_from, lang_to=lang_to)

        if suffix == ".pdf":
            nodes = generate_framework(course_name=course, pdf_path=tmp_path, **lang_kwargs)
        else:
            nodes = generate_framework(course_name=course, docx_path=tmp_path, **lang_kwargs)

        (course_dir / "framework.json").write_text(
            json.dumps([asdict(n) for n in nodes], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if mode == "review":
            full_text = _extract_full(tmp_path, suffix)
            (course_dir / "source.txt").write_text(full_text, encoding="utf-8")
            rhetoric_data = extract_rhetoric_chunked(course, full_text, **lang_kwargs)
            rhetoric = [
                RhetoricEntry(id=str(uuid.uuid4()), courses=[course], **r)
                for r in rhetoric_data
            ]
            (course_dir / "rhetoric.json").write_text(
                json.dumps([asdict(r) for r in rhetoric], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        md_content = to_mubu_markdown(nodes)
        out_path = course_dir / "export_mubu.md"
        out_path.write_text(md_content, encoding="utf-8")

        _jobs[job_id] = {"status": "done", "result_path": str(out_path), "course": course}
    except Exception as e:
        _jobs[job_id] = {"status": "error", "error": str(e)}
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@app.get("/", response_class=HTMLResponse)
async def index():
    return Path("static/index.html").read_text(encoding="utf-8")


@app.post("/generate")
def generate(
    course: str = Form(...),
    mode: str = Form(default="fill"),
    pdf: UploadFile = File(...),
    lang_mode: str = Form(default="original"),
    lang_from: str = Form(default="auto"),
    lang_to: str = Form(default="zh"),
):
    suffix = Path(pdf.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="请上传 PDF 或 Word (.docx) 文件")

    content = pdf.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="文件超过 20MB，请压缩后重试")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "processing"}

    thread = threading.Thread(
        target=_process_job,
        args=(job_id, tmp_path, suffix, course, mode, lang_mode, lang_from, lang_to),
        daemon=True,
    )
    thread.start()

    return JSONResponse({"job_id": job_id})


@app.get("/status/{job_id}")
def status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    return JSONResponse(job)


@app.get("/download/{job_id}")
def download(job_id: str):
    job = _jobs.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="文件未就绪")
    return FileResponse(
        path=job["result_path"],
        filename=f"{job['course']}_幕布框架.md",
        media_type="text/markdown; charset=utf-8",
    )
