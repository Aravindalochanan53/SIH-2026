"""
Video Translation API Router for TRANSLARA.
"""
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.services.subtitle_service import generate_srt, generate_webvtt
from backend.services.video_service import VideoJob, get_video_service

router = APIRouter(prefix="/api/video", tags=["Video Translation"])


class VideoTranslateRequest(BaseModel):
    job_id: str
    source_lang: str = "ta"
    target_lang: str = "ml"


class DemoVideoRequest(BaseModel):
    source_lang: str = "ta"
    target_lang: str = "ml"


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    source_lang: str = Form("ta"),
    target_lang: str = Form("ml"),
):
    """Upload a prerecorded classroom lesson or lecture video (.mp4, .webm, .mov)."""
    allowed_exts = {".mp4", ".webm", ".mov", ".mkv"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Supported: MP4, WebM, MOV, MKV",
        )

    file_bytes = await file.read()
    video_service = get_video_service()
    job = video_service.create_job(
        file_bytes=file_bytes,
        filename=file.filename or "video.mp4",
        source_lang=source_lang,
        target_lang=target_lang,
    )
    return job.to_dict()


@router.post("/translate")
async def start_video_translation(
    req: VideoTranslateRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger asynchronous background video translation pipeline."""
    video_service = get_video_service()
    job = video_service.get_job(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")

    job.source_language = req.source_lang
    job.target_language = req.target_lang

    # Launch in background
    background_tasks.add_task(video_service.process_video, req.job_id)
    return {
        "status": "processing_started",
        "job_id": req.job_id,
        "message": "Video translation initiated in background",
    }


@router.post("/demo")
async def trigger_demo_video(
    req: DemoVideoRequest,
    background_tasks: BackgroundTasks,
):
    """Instantly create and translate a sample classroom lesson for SIH judge demos."""
    video_service = get_video_service()
    dummy_bytes = b"TRANSLARA_DEMO_VIDEO_STREAM"
    job = video_service.create_job(
        file_bytes=dummy_bytes,
        filename="classroom_lesson_numbers.mp4",
        source_lang=req.source_lang,
        target_lang=req.target_lang,
    )

    background_tasks.add_task(video_service.process_video, job.job_id)
    return job.to_dict()


@router.get("/status/{job_id}")
async def get_video_status(job_id: str):
    """Poll video translation status and progress."""
    video_service = get_video_service()
    job = video_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")
    return job.to_dict()


@router.get("/subtitles/{job_id}")
async def get_subtitles(job_id: str, format: str = "vtt", mode: str = "dual"):
    """Download or stream generated subtitles in WebVTT or SRT format."""
    video_service = get_video_service()
    job = video_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")

    from backend.services.subtitle_service import SubtitleSegment

    segments = [
        SubtitleSegment(
            index=s["index"],
            start_seconds=s["start_seconds"],
            end_seconds=s["end_seconds"],
            source_text=s["source_text"],
            target_text=s["target_text"],
        )
        for s in job.segments
    ]

    if format.lower() == "srt":
        content = generate_srt(segments, mode)
        return Response(content=content, media_type="text/plain; charset=utf-8")
    else:
        content = generate_webvtt(segments, mode)
        return Response(content=content, media_type="text/vtt; charset=utf-8")


@router.get("/history")
async def list_video_history():
    """List all translated videos and active jobs."""
    video_service = get_video_service()
    jobs = video_service.list_jobs()
    return [j.to_dict() for j in jobs]
