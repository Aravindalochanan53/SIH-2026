#!/usr/bin/env python3
"""
TRANSLARA — Full Video Translation CLI Tool.

Translates an entire video file from start to finish:
1. Audio extraction (FFmpeg)
2. Speech recognition & sentence timestamping (Faster-Whisper CUDA FP16 / CPU INT8)
3. High-speed multilingual translation (Google API / Neural Engine)
4. Subtitle generation (.srt and .vtt)
5. Neural voice dubbing timeline (Edge-TTS & gTTS)
6. Final video remuxing with audio-video sync

Usage:
    python translate_video.py --input "path/to/video.mp4" --source ta --target ml
    python translate_video.py --input "path/to/video.mp4" --source en --target ta --output "translated.mp4"
"""
import argparse
import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

import imageio_ffmpeg
import numpy as np
import scipy.io.wavfile as wavfile


def ensure_cuda_dlls():
    """Ensure torch/lib CUDA DLLs are found on Windows for ctranslate2 / faster-whisper."""
    try:
        import torch
        torch_lib = os.path.join(os.path.dirname(torch.__file__), "lib")
        if os.path.exists(torch_lib):
            if hasattr(os, "add_dll_directory"):
                try:
                    os.add_dll_directory(torch_lib)
                except Exception:
                    pass
            os.environ["PATH"] = torch_lib + os.pathsep + os.environ.get("PATH", "")
    except Exception as e:
        print(f"[Notice] CUDA DLL discovery: {e}")


ensure_cuda_dlls()

# Language display names
LANG_NAMES = {
    "ta": "Tamil (தமிழ்)",
    "ml": "Malayalam (മലയാളം)",
    "te": "Telugu (తెలుగు)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "hi": "Hindi (हिन्दी)",
    "bn": "Bengali (বাংলা)",
    "mr": "Marathi (मराठी)",
    "gu": "Gujarati (ગુજરાતી)",
    "ur": "Urdu (اردو)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)",
    "en": "English",
}

EDGE_VOICES = {
    "ta": "ta-IN-PallaviNeural",
    "ml": "ml-IN-SobhanaNeural",
    "te": "te-IN-MohanNeural",
    "kn": "kn-IN-GaganNeural",
    "hi": "hi-IN-MadhurNeural",
    "bn": "bn-IN-TanishaaNeural",
    "mr": "mr-IN-AarohiNeural",
    "gu": "gu-IN-NiranjanNeural",
    "ur": "ur-IN-GulNeural",
    "en": "en-IN-NeerjaNeural",
}

GTTS_LANG_MAP = {
    "ta": "ta", "ml": "ml", "te": "te", "kn": "kn",
    "hi": "hi", "bn": "bn", "mr": "mr", "gu": "gu",
    "ur": "ur", "en": "en",
}


def get_media_duration(file_path: Path, ffmpeg_exe: str) -> float:
    """Extract media duration in seconds."""
    try:
        cmd = [ffmpeg_exe, "-i", str(file_path)]
        res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                parts = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = parts.split(":")
                return float(h) * 3600 + float(m) * 60 + float(s)
    except Exception:
        pass
    return 0.0


def format_timestamp(seconds: float, vtt: bool = False) -> str:
    """Format seconds into HH:MM:SS,mmm or HH:MM:SS.mmm."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    sep = "." if vtt else ","
    return f"{hrs:02d}:{mins:02d}:{secs:02d}{sep}{millis:03d}"


def save_subtitles_files(segments: List[dict], srt_path: Path, vtt_path: Path):
    """Save SRT and WebVTT subtitle files."""
    srt_lines = []
    vtt_lines = ["WEBVTT", ""]

    for s in segments:
        idx = s["index"]
        t_start_srt = format_timestamp(s["start"], vtt=False)
        t_end_srt = format_timestamp(s["end"], vtt=False)
        t_start_vtt = format_timestamp(s["start"], vtt=True)
        t_end_vtt = format_timestamp(s["end"], vtt=True)

        # Dual subtitle format: Source on line 1, Translated on line 2
        dual_text = f"{s['source_text']}\n{s['target_text']}"

        srt_lines.extend([str(idx), f"{t_start_srt} --> {t_end_srt}", dual_text, ""])
        vtt_lines.extend([str(idx), f"{t_start_vtt} --> {t_end_vtt}", dual_text, ""])

    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
    vtt_path.write_text("\n".join(vtt_lines), encoding="utf-8")


async def synthesize_dubbing_track(
    segments: List[dict],
    target_lang: str,
    total_duration: float,
    work_dir: Path,
    ffmpeg_exe: str,
) -> Optional[Path]:
    """Synthesize speech for each segment and position on full audio timeline."""
    clean_lang = (target_lang or "").lower().strip()
    edge_voice = EDGE_VOICES.get(clean_lang, "hi-IN-MadhurNeural")
    gtts_lang = GTTS_LANG_MAP.get(clean_lang, "hi")

    has_edge_tts = False
    try:
        import edge_tts
        has_edge_tts = True
    except ImportError:
        pass

    sample_rate = 24000
    max_end = max((s["end"] for s in segments), default=1.0)
    timeline_dur = max(total_duration, max_end, 1.0)
    total_samples = int(timeline_dur * sample_rate) + (sample_rate * 5)
    timeline = np.zeros(total_samples, dtype=np.int16)

    print(f"[*] Synthesizing neural voice clips for {len(segments)} segments...")

    for s in segments:
        idx = s["index"]
        text = (s.get("target_text") or "").strip()
        if not text:
            continue

        mp3_file = work_dir / f"seg_{idx}.mp3"
        wav_file = work_dir / f"seg_{idx}.wav"

        synth_ok = False
        if has_edge_tts:
            try:
                communicate = edge_tts.Communicate(text, voice=edge_voice)
                await communicate.save(str(mp3_file))
                if mp3_file.exists() and mp3_file.stat().st_size > 100:
                    synth_ok = True
            except Exception:
                pass

        if not synth_ok:
            try:
                from gtts import gTTS
                tts = gTTS(text=text, lang=gtts_lang, slow=False)
                tts.save(str(mp3_file))
                if mp3_file.exists() and mp3_file.stat().st_size > 100:
                    synth_ok = True
            except Exception as ex:
                print(f"    [Warning] TTS segment {idx} failed: {ex}")

        if not synth_ok or not mp3_file.exists():
            continue

        # Convert to 24kHz mono WAV
        cmd = [ffmpeg_exe, "-y", "-i", str(mp3_file), "-ar", str(sample_rate), "-ac", "1", str(wav_file)]
        subprocess.run(cmd, capture_output=True)

        if not wav_file.exists():
            continue

        try:
            _, data = wavfile.read(str(wav_file))
            start_sec = float(s["start"])
            start_idx = int(start_sec * sample_rate)

            needed = start_idx + len(data)
            if needed > len(timeline):
                timeline = np.pad(timeline, (0, needed - len(timeline) + (sample_rate * 5)))

            existing = timeline[start_idx : start_idx + len(data)].astype(np.int32)
            incoming = data.astype(np.int32)
            timeline[start_idx : start_idx + len(data)] = np.clip(existing + incoming, -32768, 32767).astype(np.int16)
        except Exception as e:
            print(f"    [Warning] Error mixing segment {idx}: {e}")

    # Export composite audio
    full_wav = work_dir / "full_dubbed.wav"
    wavfile.write(str(full_wav), sample_rate, timeline)

    full_aac = work_dir / "full_dubbed.aac"
    enc_cmd = [ffmpeg_exe, "-y", "-i", str(full_wav), "-c:a", "aac", "-b:a", "192k", str(full_aac)]
    subprocess.run(enc_cmd, capture_output=True, check=True)

    if full_wav.exists():
        full_wav.unlink()

    return full_aac


async def async_main():
    parser = argparse.ArgumentParser(description="TRANSLARA: Complete Video Translation CLI")
    parser.add_argument("--input", "-i", required=True, help="Input video file path (.mp4, .mkv, .webm, .mov)")
    parser.add_argument("--source", "-s", default="auto", help="Source language code (e.g. ta, hi, en, auto)")
    parser.add_argument("--target", "-t", default="ml", help="Target language code (e.g. ml, ta, hi, en, te, kn)")
    parser.add_argument("--output", "-o", default=None, help="Output translated video path (optional)")
    parser.add_argument("--device", "-d", default="cuda", choices=["cuda", "cpu"], help="Inference device for ASR")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"[Error] Input video file not found: {input_path}")
        sys.exit(1)

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    total_dur = get_media_duration(input_path, ffmpeg_exe)
    print("=" * 65)
    print(" TRANSLARA — Complete Video Translation Engine")
    print("=" * 65)
    print(f"[*] Input File     : {input_path.name}")
    print(f"[*] Size           : {input_path.stat().st_size / (1024*1024):.2f} MB")
    print(f"[*] Duration       : {total_dur:.2f} seconds ({int(total_dur//60)}m {int(total_dur%60)}s)")
    print(f"[*] Translation    : {args.source.upper()} ({LANG_NAMES.get(args.source, args.source)}) -> {args.target.upper()} ({LANG_NAMES.get(args.target, args.target)})")
    print(f"[*] Device         : {args.device.upper()}")
    print("=" * 65)

    # Output directory
    output_dir = input_path.parent / f"{input_path.stem}_translated_{args.target}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Audio Extraction
    print("\n[Stage 1/5] Extracting audio track...")
    t0 = time.time()
    audio_wav = output_dir / "extracted_audio.wav"
    ext_cmd = [
        ffmpeg_exe, "-y", "-i", str(input_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(audio_wav),
    ]
    subprocess.run(ext_cmd, capture_output=True, check=True)
    print(f"    Audio extracted in {time.time() - t0:.2f}s -> {audio_wav.name}")

    # 2. Transcription with Faster-Whisper
    print("\n[Stage 2/5] Transcribing speech across entire video with sentence timestamps...")
    t0 = time.time()
    from faster_whisper import WhisperModel
    whisper_cache = Path(__file__).resolve().parent / "models"
    whisper_snap = whisper_cache / "models--Systran--faster-whisper-small" / "snapshots" / "536b0662742c02347bc0e980a01041f333bce120"
    model_path = str(whisper_snap) if whisper_snap.exists() else "small"

    device = args.device
    compute_type = "float16" if device == "cuda" else "int8"

    whisper = None
    try:
        whisper = WhisperModel(model_path, device=device, compute_type=compute_type, download_root=str(whisper_cache))
    except Exception as e:
        print(f"    [Warning] Failed loading on {device} ({e}); falling back to CPU int8")
        whisper = WhisperModel(model_path, device="cpu", compute_type="int8", download_root=str(whisper_cache))

    lang_arg = None if args.source in ("auto", "", None) else args.source
    segments_gen, info = whisper.transcribe(
        str(audio_wav),
        language=lang_arg,
        vad_filter=True,
        beam_size=1,
        condition_on_previous_text=False,
    )

    raw_segments = []
    print(f"    Detected language: {info.language} (confidence: {info.language_probability:.2%})")
    for s in segments_gen:
        t = s.text.strip()
        if t:
            raw_segments.append({"start": s.start, "end": s.end, "text": t})
            print(f"    [{s.start:6.1f}s -> {s.end:6.1f}s] {t}")

    print(f"    Total dialogue segments transcribed: {len(raw_segments)} in {time.time() - t0:.2f}s")

    if not raw_segments:
        print("[!] No spoken dialogue detected in audio track. Preserving original audio.")
        sys.exit(0)

    # 3. Multilingual Translation
    print(f"\n[Stage 3/5] Translating {len(raw_segments)} segments into {args.target.upper()}...")
    t0 = time.time()
    from backend.ai.translation.google_api_provider import get_google_provider
    google_provider = get_google_provider()

    source_texts = [s["text"] for s in raw_segments]
    src_code = info.language if args.source == "auto" else args.source
    translated_texts = await google_provider.translate_batch(
        texts=source_texts,
        source_lang=src_code,
        target_lang=args.target,
        concurrency=16,
    )

    processed_segments = []
    for idx, (rseg, trans_text) in enumerate(zip(raw_segments, translated_texts), start=1):
        processed_segments.append({
            "index": idx,
            "start": round(rseg["start"], 2),
            "end": round(rseg["end"], 2),
            "source_text": rseg["text"],
            "target_text": trans_text or rseg["text"],
        })

    print(f"    All {len(processed_segments)} segments translated in {time.time() - t0:.2f}s")

    # 4. Generate Subtitles (.srt and .vtt)
    print("\n[Stage 4/5] Generating synchronized subtitles (.srt and .vtt)...")
    srt_path = output_dir / f"{input_path.stem}_{args.target}.srt"
    vtt_path = output_dir / f"{input_path.stem}_{args.target}.vtt"
    save_subtitles_files(processed_segments, srt_path, vtt_path)
    print(f"    SRT Subtitles  : {srt_path.name}")
    print(f"    WebVTT Subtitles: {vtt_path.name}")

    # 5. Neural Dubbing & Video Muxing
    print("\n[Stage 5/5] Synthesizing translated neural speech & remuxing video...")
    t0 = time.time()
    dubbed_audio_path = await synthesize_dubbing_track(
        segments=processed_segments,
        target_lang=args.target,
        total_duration=total_dur,
        work_dir=output_dir,
        ffmpeg_exe=ffmpeg_exe,
    )

    final_video_name = args.output or (output_dir / f"{input_path.stem}_translated_{args.target}.mp4")
    final_video_path = Path(final_video_name).resolve()

    mux_cmd = [
        ffmpeg_exe, "-y",
        "-i", str(input_path),
        "-i", str(dubbed_audio_path),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(final_video_path),
    ]
    subprocess.run(mux_cmd, capture_output=True, check=True)
    print(f"    Video remuxed in {time.time() - t0:.2f}s -> {final_video_path.name}")

    print("\n" + "=" * 65)
    print(" COMPLETE VIDEO TRANSLATION SUCCESSFUL!")
    print("=" * 65)
    print(f"[✓] Translated Video : {final_video_path}")
    print(f"[✓] Subtitles (SRT)  : {srt_path}")
    print(f"[✓] Subtitles (VTT)  : {vtt_path}")
    print(f"[✓] Dubbed Audio AAC : {dubbed_audio_path}")
    print(f"[✓] Total Segments   : {len(processed_segments)}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(async_main())
