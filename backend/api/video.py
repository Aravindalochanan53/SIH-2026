"""
Video Translation API Router for TRANSLARA with MSSQL Job Tracking.
"""
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_optional_user
from backend.database.models import User
from backend.database.repositories.video_repo import VideoRepository
from backend.database.session import get_db
from backend.services.subtitle_service import generate_srt, generate_webvtt
from backend.services.video_service import VideoJob as MemVideoJob, get_video_service

router = APIRouter(prefix="/api/video", tags=["Video Translation"])


class VideoTranslateRequest(BaseModel):
    job_id: str
    source_lang: str = "ta"
    target_lang: str = "ml"


class DemoVideoRequest(BaseModel):
    source_lang: str = "ta"
    target_lang: str = "ml"


@router.post("/upload")
def upload_video(
    file: UploadFile = File(...),
    source_lang: str = Form("ta"),
    target_lang: str = Form("ml"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Upload a prerecorded classroom lesson or lecture video (.mp4, .webm, .mov)."""
    allowed_exts = {".mp4", ".webm", ".mov", ".mkv"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Supported: MP4, WebM, MOV, MKV",
        )

    file_bytes = file.file.read()
    video_service = get_video_service()
    job = video_service.create_job(
        file_bytes=file_bytes,
        filename=file.filename or "video.mp4",
        source_lang=source_lang,
        target_lang=target_lang,
    )

    # Save job metadata in MSSQL
    try:
        video_repo = VideoRepository(db)
        video_repo.create_job(
            job_id=job.job_id,
            original_filename=file.filename or "video.mp4",
            source_language=source_lang,
            target_language=target_lang,
            input_path=str(job.input_video_path) if job.input_video_path else None,
            user_id=user.id if user else None,
        )
    except Exception:
        pass

    return job.to_dict()


@router.post("/translate")
def start_video_translation(
    req: VideoTranslateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger asynchronous background video translation pipeline."""
    video_service = get_video_service()
    job = video_service.get_job(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")

    job.source_language = req.source_lang
    job.target_language = req.target_lang

    # Update status in MSSQL
    try:
        video_repo = VideoRepository(db)
        video_repo.update_job_status(job_id=req.job_id, status="processing", progress=0.1)
    except Exception:
        pass

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
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
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

    try:
        video_repo = VideoRepository(db)
        video_repo.create_job(
            job_id=job.job_id,
            original_filename="classroom_lesson_numbers.mp4",
            source_language=req.source_lang,
            target_language=req.target_lang,
            user_id=user.id if user else None,
        )
    except Exception:
        pass

    background_tasks.add_task(video_service.process_video, job.job_id)
    return job.to_dict()


@router.get("/status/{job_id}")
def get_video_status(job_id: str):
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


@router.get("/stream/{job_id}")
@router.get("/stream/{job_id}/{video_type}")
async def stream_video(job_id: str, video_type: str = "translated"):
    """Stream original or translated video for web playback."""
    video_service = get_video_service()
    job = video_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")

    target_path = job.output_video_path if video_type == "translated" and job.output_video_path else job.input_video_path
    if not target_path or not Path(target_path).exists():
        if job.input_video_path and Path(job.input_video_path).exists():
            target_path = job.input_video_path
        else:
            raise HTTPException(status_code=404, detail="Video media file not found")

    return FileResponse(
        path=target_path,
        media_type="video/mp4",
        filename=Path(target_path).name,
    )


@router.get("/audio/{job_id}/translated")
async def stream_translated_audio(job_id: str):
    """Stream synthesized translated voice audio for the video."""
    video_service = get_video_service()
    job = video_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")

    if job.translated_audio_path and Path(job.translated_audio_path).exists():
        return FileResponse(
            path=job.translated_audio_path,
            media_type="audio/mpeg",
            filename=f"{job_id}_translated_voice.mp3",
        )
    raise HTTPException(status_code=404, detail="Translated voice audio track not found")


@router.get("/audio/{job_id}/segment/{index}")
async def stream_segment_audio(job_id: str, index: int):
    """Stream synthesized translated voice audio for a specific segment."""
    video_service = get_video_service()
    job = video_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")

    from backend.config import settings
    job_dir = Path(settings.data_dir) / "videos" / job_id
    seg_file = job_dir / f"seg_voice_{index}.mp3"
    if seg_file.exists():
        return FileResponse(
            path=str(seg_file),
            media_type="audio/mpeg",
            filename=f"segment_{index}_voice.mp3",
        )
    raise HTTPException(status_code=404, detail="Segment audio not found")


@router.get("/download/{job_id}/{format}")
async def download_video_assets(job_id: str, format: str):
    """Download translated video file or subtitles (srt, vtt, mp4)."""
    video_service = get_video_service()
    job = video_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Video job not found")

    fmt = format.lower()
    if fmt == "srt":
        if not job.subtitle_srt_path or not Path(job.subtitle_srt_path).exists():
            from backend.services.subtitle_service import SubtitleSegment
            sub_segs = [
                SubtitleSegment(
                    index=s["index"],
                    start_seconds=s["start_seconds"],
                    end_seconds=s["end_seconds"],
                    source_text=s["source_text"],
                    target_text=s.get("target_text", s.get("translated_text", "")),
                )
                for s in job.segments
            ]
            content = generate_srt(sub_segs, mode="dual")
            return Response(
                content=content,
                media_type="application/x-subrip",
                headers={"Content-Disposition": f'attachment; filename="{job_id}_subtitles.srt"'},
            )
        return FileResponse(
            path=job.subtitle_srt_path,
            filename=f"{job_id}_subtitles.srt",
            media_type="application/x-subrip",
        )

    elif fmt == "vtt":
        if not job.subtitle_vtt_path or not Path(job.subtitle_vtt_path).exists():
            from backend.services.subtitle_service import SubtitleSegment
            sub_segs = [
                SubtitleSegment(
                    index=s["index"],
                    start_seconds=s["start_seconds"],
                    end_seconds=s["end_seconds"],
                    source_text=s["source_text"],
                    target_text=s.get("target_text", s.get("translated_text", "")),
                )
                for s in job.segments
            ]
            content = generate_webvtt(sub_segs, mode="dual")
            return Response(
                content=content,
                media_type="text/vtt",
                headers={"Content-Disposition": f'attachment; filename="{job_id}_subtitles.vtt"'},
            )
        return FileResponse(
            path=job.subtitle_vtt_path,
            filename=f"{job_id}_subtitles.vtt",
            media_type="text/vtt",
        )

    elif fmt in ("mp4", "video"):
        path = job.output_video_path if job.output_video_path and Path(job.output_video_path).exists() else job.input_video_path
        if not path or not Path(path).exists():
            raise HTTPException(status_code=404, detail="Video file not available for download")
        return FileResponse(
            path=path,
            filename=f"{job_id}_translated.mp4",
            media_type="video/mp4",
        )

    raise HTTPException(status_code=400, detail=f"Unsupported download format: {format}")


@router.get("/history")
def list_video_history():
    """List all translated videos and active jobs with instant response."""
    video_service = get_video_service()
    jobs = video_service.list_jobs()
    return [j.to_dict() for j in jobs]
