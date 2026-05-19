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
from fill_mode.parser import extract_text_from_pdf
from review_mode.rhetoric import extract_rhetoric_chunked
from store.schema import RhetoricEntry

app = FastAPI()
DATA_DIR = Path(os.getenv("STUDYMAP_DATA_DIR", "./data"))


@app.get("/", response_class=HTMLResponse)
async def index():
    return Path("static/index.html").read_text(encoding="utf-8")


@app.post("/generate")
def generate(
    course: str = Form(...),
    mode: str = Form(default="fill"),
    pdf: UploadFile = File(...),
):
    if not pdf.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="请上传 PDF 文件")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(pdf.file, tmp)
        tmp_path = tmp.name

    try:
        course_dir = DATA_DIR / course.replace(" ", "_")
        course_dir.mkdir(parents=True, exist_ok=True)

        # 生成知识框架（两种模式都需要，均只用前25页）
        try:
            nodes = generate_framework(course_name=course, pdf_path=tmp_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"框架生成失败：{e}")

        (course_dir / "framework.json").write_text(
            json.dumps([asdict(n) for n in nodes], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # 复习模式：额外对全文做分块话术提取
        if mode == "review":
            try:
                full_text = extract_text_from_pdf(tmp_path)
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
