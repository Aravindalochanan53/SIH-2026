# TRANSLARA — API Reference

Base URL: `http://localhost:8000`

---

## 1. Text Translation
### `POST /api/translate`
```json
// Request
{
  "text": "வணக்கம்",
  "source_language": "ta",
  "target_language": "ml"
}

// Response (HTTP 200)
{
  "success": true,
  "original_text": "வணக்கம்",
  "translation": "നമസ്കാരം",
  "source_language": "ta",
  "target_language": "ml",
  "engine": "offline_dataset",
  "offline": true,
  "pivot_translation": false,
  "latency_ms": 2.59
}
```

---

## 2. Voice & Speech
- `GET /api/voice/status` — Audio stream parameters and connection status.
- `POST /api/voice/synthesize` — Synthesize speech for target text.
- `WebSocket /ws/live-stream` — Real-time bidirectional speech streaming.

---

## 3. Video Translation
- `POST /api/video/upload` — Upload video (`multipart/form-data`).
- `POST /api/video/translate` — Start video translation job.
- `GET /api/video/jobs/{job_id}` — Query job status and URLs.
- `GET /api/video/jobs/{job_id}/subtitles` — Download `.srt` or `.vtt` subtitles.

---

## 4. AI Chatbot & Pedagogy
- `POST /api/chat/message` — Send classroom query or translation prompt.
- `GET /api/chat/history` — Fetch conversation history.
- `POST /api/pedagogy/worksheet/generate` — Generate bilingual printable A4 FLN PDF worksheet.
- `POST /api/pedagogy/flashcards/generate` — Generate classroom flashcard deck.

---

## 5. System & Languages
- `GET /api/languages` — List registered pan-Indian languages.
- `GET /api/capabilities` — Query active ASR, NMT, TTS backend matrices.
- `GET /health` — Subsystem health and latency checks.
