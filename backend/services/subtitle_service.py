"""
Subtitle Generation Service for TRANSLARA.

Supports WebVTT (.vtt) and SubRip (.srt) generation for single and dual-language subtitles.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class SubtitleSegment:
    index: int
    start_seconds: float
    end_seconds: float
    source_text: str
    target_text: str


def format_timestamp(seconds: float, vtt: bool = False) -> str:
    """Format seconds into HH:MM:SS,mmm (SRT) or HH:MM:SS.mmm (VTT)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)

    sep = "." if vtt else ","
    return f"{hrs:02d}:{mins:02d}:{secs:02d}{sep}{millis:03d}"


def generate_srt(segments: list[SubtitleSegment], mode: str = "target") -> str:
    """
    Generate SRT subtitle string.
    mode: 'target' | 'source' | 'dual'
    """
    lines: list[str] = []
    for seg in segments:
        lines.append(str(seg.index))
        t_start = format_timestamp(seg.start_seconds, vtt=False)
        t_end = format_timestamp(seg.end_seconds, vtt=False)
        lines.append(f"{t_start} --> {t_end}")

        if mode == "source":
            lines.append(seg.source_text)
        elif mode == "dual":
            lines.append(f"{seg.source_text}\n{seg.target_text}")
        else:  # target
            lines.append(seg.target_text)

        lines.append("")  # Empty line separator

    return "\n".join(lines)


def generate_webvtt(segments: list[SubtitleSegment], mode: str = "target") -> str:
    """
    Generate WebVTT subtitle string.
    mode: 'target' | 'source' | 'dual'
    """
    lines: list[str] = ["WEBVTT", ""]
    for seg in segments:
        t_start = format_timestamp(seg.start_seconds, vtt=True)
        t_end = format_timestamp(seg.end_seconds, vtt=True)
        lines.append(f"{seg.index}")
        lines.append(f"{t_start} --> {t_end}")

        if mode == "source":
            lines.append(seg.source_text)
        elif mode == "dual":
            lines.append(f"{seg.source_text}\n{seg.target_text}")
        else:  # target
            lines.append(seg.target_text)

        lines.append("")

    return "\n".join(lines)


def save_subtitles(
    segments: list[SubtitleSegment],
    out_base_path: Path,
    mode: str = "target",
) -> tuple[Path, Path]:
    """Save both SRT and VTT subtitle files and return paths."""
    out_base_path.parent.mkdir(parents=True, exist_ok=True)
    srt_path = out_base_path.with_suffix(".srt")
    vtt_path = out_base_path.with_suffix(".vtt")

    srt_path.write_text(generate_srt(segments, mode), encoding="utf-8")
    vtt_path.write_text(generate_webvtt(segments, mode), encoding="utf-8")

    return srt_path, vtt_path
