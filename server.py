import json
import os
import shutil
import tempfile
import uuid
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from fill_mode.framework import generate_framework
from fill_mode.mubu_export import to_mubu_markdown
from fill_mode.parser import (
    extract_text_from_pdf,
    extract_first_pages,
    extract_text_from_docx,
    extract_first_paras_docx,
)
from review_mode.rhetoric import extract_rhetoric_chunked
from store.schema import RhetoricEntry

app = FastAPI()
DATA_DIR = Path(os.getenv("STUDYMAP_DATA_DIR", "./data"))

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def _extract_for_fill(tmp_path: str, suffix: str) -> str:
    if suffix == ".pdf":
        return extract_first_pages(tmp_path, n=25)
    return extract_first_paras_docx(tmp_path, n=200)


def _extract_full(tmp_path: str, suffix: str) -> str:
    if suffix == ".pdf":
        return extract_text_from_pdf(tmp_path)
    return extract_text_from_docx(tmp_path)


@app.get("/", response_class=HTMLResponse)
async def index():
    return Path("static/index.html").read_text(encoding="utf-8")


@app.post("/generate")
def generate(
    course: str = Form(...),
    mode: str = Form(default="fill"),
    pdf: UploadFile = File(...),
):
    suffix = Path(pdf.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="请上传 PDF 或 Word (.docx) 文件")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = pdf.file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="文件超过 20MB，请压缩后重试")
        tmp.write(content)
        tmp_path = tmp.name

    try:
        course_dir = DATA_DIR / course.replace(" ", "_")
        course_dir.mkdir(parents=True, exist_ok=True)

        try:
            fill_text = _extract_for_fill(tmp_path, suffix)
            nodes = generate_framework(course_name=course, material_text=fill_text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"框架生成失败：{e}")

        (course_dir / "framework.json").write_text(
            json.dumps([asdict(n) for n in nodes], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if mode == "review":
            try:
                full_text = _extract_full(tmp_path, suffix)
                (course_dir / "source.txt").write_text(full_text, encoding="utf-8")
                rhetoric_data = extract_rhetoric_chunked(course, full_text)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"话术提取失败：{e}")

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

        return FileResponse(
            path=str(out_path),
            filename=f"{course}_幕布框架.md",
            media_type="text/markdown; charset=utf-8",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败：{e}")
    finally:
        os.unlink(tmp_path)
