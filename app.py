from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import json
import os
import glob
from fastapi.responses import StreamingResponse
from fastapi import Header, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
app = FastAPI()

# 정적 파일 서빙 (css, js, img 등)
app.mount("/static", StaticFiles(directory="."), name="static")
app.mount("/output", StaticFiles(directory="output"), name="videos")

VIDEO_PATH = "./output/tracked_video.mp4"  # main.py가 생성하는 영상 파일명

def get_latest_json_file():
    json_dir = "./output/json"
    json_files = glob.glob(os.path.join(json_dir, "*.json"))
    if not json_files:
        return None
    latest_file = max(json_files, key=os.path.getctime)
    return latest_file

@app.get("/analyze", response_class=HTMLResponse)
def get_analze_html():
    with open("analyze.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/video")
def stream_video(range: str = Header(None)):
    path = VIDEO_PATH
    file_size = os.path.getsize(path)

    if not range:
        return FileResponse(path, media_type="video/mp4")

    # "bytes=start-end"
    start_str, end_str = range.replace("bytes=", "").split("-")
    start = int(start_str)
    end   = int(end_str) if end_str else file_size - 1

    if start >= file_size or end >= file_size:
        raise HTTPException(416, "Requested Range Not Satisfiable")

    def chunker():
        with open(path, "rb") as f:
            f.seek(start)
            # 한 번에 통째로 읽어서 한 번만 yield
            chunk = f.read(end - start + 1)
            if chunk:
                yield chunk

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
    }
    return StreamingResponse(
        chunker(),
        status_code=206,
        headers=headers,
        media_type="video/mp4",
    )


@app.get("/info")
def get_info():
    json_path = get_latest_json_file()
    if json_path is None:
        return JSONResponse(content={"error": "json 파일이 없습니다."}, status_code=404)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(content=data)

from fastapi.responses import FileResponse

@app.get("/download/video")
def download_video():
    return FileResponse(
        path=VIDEO_PATH,
        media_type="application/octet-stream",
        filename="tracked_video.mp4",  # 저장될 기본 파일명
    )

@app.get("/download/info")
def download_info():
    json_path = get_latest_json_file()
    if not json_path:
        return JSONResponse({"error": "json 파일이 없습니다."}, status_code=404)
    return FileResponse(
        path=json_path,
        media_type="application/json",
        filename=os.path.basename(json_path),
    )
