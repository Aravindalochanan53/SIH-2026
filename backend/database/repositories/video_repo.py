"""
Video Translation Job Repository for TRANSLARA Database.
"""
from __future__ import annotations

import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import VideoJob


class VideoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_job(
        self,
        job_id: str,
        filename: str,
        source_language: str,
        target_language: str,
        original_video_url: Optional[str] = None,
    ) -> VideoJob:
        job = VideoJob(
            id=job_id,
            filename=filename,
            source_language=source_language,
            target_language=target_language,
            status="PENDING",
            progress=0.0,
            original_video_url=original_video_url,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: str) -> Optional[VideoJob]:
        return self.db.query(VideoJob).filter(VideoJob.id == job_id).first()

    def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: float,
        translated_video_url: Optional[str] = None,
        subtitles_srt_url: Optional[str] = None,
        subtitles_vtt_url: Optional[str] = None,
        transcript_url: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[VideoJob]:
        job = self.get_job(job_id)
        if not job:
            return None

        job.status = status
        job.progress = progress
        if translated_video_url:
            job.translated_video_url = translated_video_url
        if subtitles_srt_url:
            job.subtitles_srt_url = subtitles_srt_url
        if subtitles_vtt_url:
            job.subtitles_vtt_url = subtitles_vtt_url
        if transcript_url:
            job.transcript_url = transcript_url
        if error_message:
            job.error_message = error_message
        if status in ("COMPLETED", "FAILED"):
            job.completed_at = datetime.datetime.utcnow()

        self.db.commit()
        self.db.refresh(job)
        return job

    def list_jobs(self, limit: int = 50) -> List[VideoJob]:
        return self.db.query(VideoJob).order_by(VideoJob.created_at.desc()).limit(limit).all()
