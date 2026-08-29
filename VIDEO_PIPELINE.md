# TRANSLARA — Video Translation Pipeline

## 1. Video Pipeline Overview
TRANSLARA automatically converts classroom video lessons between Indian languages with audio extraction, neural translation, speech re-synthesis, and subtitle alignment.

```
Upload Video (.mp4/.webm/.mov)
       ↓
Extract Audio (FFmpeg -> 16kHz mono WAV)
       ↓
ASR Transcription (Faster-Whisper)
       ↓
Sentence & Timestamp Segmentation
       ↓
Entity Lock & NMT Translation
       ↓
Target Language TTS Synthesis
       ↓
Audio Replacement & Subtitle Overlay (SRT/VTT)
       ↓
Translated Video (MP4)
```

---

## 2. API Endpoints
- `POST /api/video/upload` — Upload raw video file.
- `POST /api/video/translate` — Start async video translation job.
- `GET /api/video/jobs/{job_id}` — Query job progress and generated URLs.
- `GET /api/video/jobs/{job_id}/subtitles?format=srt|vtt` — Download generated subtitle files.

---

## 3. Supported Input & Output Formats
- **Input Formats:** `.mp4`, `.webm`, `.mov`, `.mkv`
- **Output Artifacts:**
  - `translated_video.mp4`
  - `subtitles.srt` (SubRip Subtitle Format)
  - `subtitles.vtt` (WebVTT Format)
  - `transcript.txt`
