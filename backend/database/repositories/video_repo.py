"""
Video Translation Job Repository for TRANSLARA MSSQL Database.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import VideoJob


class VideoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_job(
        self,
        job_id: str,
        original_filename: str,
        source_language: str,
        target_language: str,
        input_path: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> VideoJob:
        job = VideoJob(
            id=job_id,
            user_id=user_id,
            original_filename=original_filename,
            source_language=source_language,
            target_language=target_language,
            status="queued",
            progress=0.0,
            input_path=input_path,
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
        progress: float = 0.0,
        output_path: Optional[str] = None,
        transcript_path: Optional[str] = None,
        subtitle_path: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[VideoJob]:
        job = self.get_job(job_id)
        if not job:
            return None

        job.status = status
        job.progress = progress
        if output_path:
            job.output_path = output_path
        if transcript_path:
            job.transcript_path = transcript_path
        if subtitle_path:
            job.subtitle_path = subtitle_path
        if error_message:
            job.error_message = error_message
        if status in ("completed", "failed"):
            job.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(job)
        return job

    def list_jobs(self, user_id: Optional[int] = None, limit: int = 50) -> List[VideoJob]:
        query = self.db.query(VideoJob)
        if user_id is not None:
            query = query.filter(VideoJob.user_id == user_id)
        return query.order_by(VideoJob.created_at.desc()).limit(limit).all()
