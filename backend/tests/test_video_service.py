"""
Unit tests for TRANSLARA Video Translation Engine & Subtitles.
"""
import pytest
from backend.services.subtitle_service import SubtitleSegment, generate_srt, generate_webvtt
from backend.services.video_service import get_video_service


def test_subtitle_generation_srt_and_vtt():
    segments = [
        SubtitleSegment(
            index=1,
            start_seconds=0.0,
            end_seconds=4.5,
            source_text="வணக்கம் மாணவர்களே",
            target_text="നമസ്കാരം വിദ്യാർത്ഥികളേ",
        ),
        SubtitleSegment(
            index=2,
            start_seconds=5.0,
            end_seconds=9.0,
            source_text="புத்தகத்தைத் திறக்கவும்",
            target_text="പുസ്തകം തുറക്കൂ",
        ),
    ]

    # Test SRT Dual Subtitles
    srt = generate_srt(segments, mode="dual")
    assert "00:00:00,000 --> 00:00:04,500" in srt
    assert "வணக்கம் மாணவர்களே" in srt
    assert "നമസ്കാരം വിദ്യാർത്ഥികളേ" in srt

    # Test WebVTT Dual Subtitles
    vtt = generate_webvtt(segments, mode="dual")
    assert "WEBVTT" in vtt
    assert "00:00:00.000 --> 00:00:04.500" in vtt


@pytest.mark.asyncio
async def test_video_service_job_lifecycle():
    service = get_video_service()
    dummy_video = b"SAMPLE_VIDEO_STREAM_BYTES"

    job = service.create_job(
        file_bytes=dummy_video,
        filename="test_lesson.mp4",
        source_lang="ta",
        target_lang="ml",
    )

    assert job.job_id is not None
    assert job.status == "UPLOADED"

    # Run processing
    await service.process_video(job.job_id)

    updated_job = service.get_job(job.job_id)
    assert updated_job.status == "COMPLETED"
    assert updated_job.progress == 100
    assert len(updated_job.segments) > 0
    assert updated_job.subtitle_vtt_path is not None
