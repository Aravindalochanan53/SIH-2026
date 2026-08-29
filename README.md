# TRANSLARA (ட்ரான்ஸ்லாரா / ట్రాన్స్‌లారా / ಟ್ರಾನ್ಸ್‌ಲಾರಾ / ട്രാൻസ്ലാറ / ट्रांसलारा)
### AI-Powered Real-Time Multilingual Speech Translation & Vernacular Education Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. Project Objective & Pan-Indian Architecture

**TRANSLARA** is an AI-powered real-time speech translation and vernacular learning system built to bridge linguistic boundaries across India. Rather than restricting translation to a single regional pair (e.g. Hindi $\rightarrow$ Tribal languages), TRANSLARA implements a **generic $SOURCE \rightarrow TARGET$ multilingual architecture** giving **first-class status to South Indian languages**:

- **South Indian Languages**:
  - **Tamil (`ta`)** — தமிழ்
  - **Telugu (`te`)** — తెలుగు
  - **Kannada (`kn`)** — ಕನ್ನಡ
  - **Malayalam (`ml`)** — മലയാളം
- **North / Other Indian Languages**:
  - **Hindi (`hi`)** — हिन्दी
  - **Santhali (`sat`)** — ᱥᱟᱱᱛᱟᱲᱤ
  - **Ho (`hoc`)** — Ho (हो)
  - **Mundari (`unr`)** — Mundari (मुंडारी)
- **Extensible Registry**: Bengali (`bn`), Marathi (`mr`), Gujarati (`gu`), Odia (`or`), Punjabi (`pa`), Assamese (`as`), Urdu (`ur`).

---

## 2. Real-Time Pipeline Workflow

```
[Speaker Speech / Tab Audio]
              │
              ▼ (16kHz PCM16 Mono via WebSocket)
    [Chrome Extension / React UI]
              │
              ▼
    [FastAPI /ws/live-stream]
              │
              ▼
       [Streaming VAD] (WebRTC VAD, 30ms frames, ~260ms tail silence)
              │
              ▼
     [Multilingual ASR] (Faster-Whisper INT8 / IndicConformer / Meta MMS)
              │
              ▼
   [Script-Agnostic Entity Lock] (⟦ENT0⟧ Shield: Names, Numbers, Cities, Math)
              │
              ▼
     [Generic NMT Engine] (AI4Bharat IndicTrans2 / Bhashini ULCA)
              │
              ▼
    [Entity Restoration] (Restores proper nouns & numerals accurately)
              │
              ▼
       [Multilingual TTS] (Indic-TTS / VITS chunked PCM16 streaming @ ~200ms)
              │
     ┌────────┴───────────────────────────┐
     ▼                                   ▼
[Audio Streamed to Student]         [Live Subtitle HUD]
(Zero-jitter audio playback)        (Bilingual subtitles with locked entities)
```

---

## 3. Centralized Language Registry & Capabilities API

All languages and model capabilities are managed through a single source of truth in `backend/ml_engine/languages.py`:
- `GET /api/languages`: Returns categorized list of supported languages (South Indian vs. North/Other Indian).
- `GET /api/capabilities`: Reports real-time backend support matrix for ASR, NMT, TTS, and offline cache for each language pair.

---

## 4. Local Quickstart & Setup

### 1. Backend Server Setup
```powershell
# 1. Clone repository
cd translara

# 2. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Copy environment configuration
Copy-Item .env.example .env

# 5. Seed database
python scripts/seed_database.py

# 6. Start FastAPI server
$env:PYTHONPATH="."
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```
FastAPI server runs on: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`
- Language Registry: `http://localhost:8000/api/languages`
- Model Capabilities: `http://localhost:8000/api/capabilities`
- Live WebSocket: `ws://localhost:8000/ws/live-stream`

### 2. Frontend Teacher Dashboard
```powershell
cd frontend
npm install
npm run dev
```
Teacher Dashboard runs on: `http://localhost:5173`

### 3. Chrome Extension (Manifest V3)
1. Open Google Chrome and navigate to: `chrome://extensions`
2. Enable **Developer mode** (top-right).
3. Click **Load unpacked** and select the `extension/` directory.

---

## 5. Demonstration Scenarios

### Scenario 1: South Indian Speech-to-Speech (Tamil ⇄ Malayalam)
1. In the Web Dashboard or Chrome Extension, select **Source**: `Tamil (தமிழ்)` and **Target**: `Malayalam (മലയാളം)`.
2. Click **Start Translation**.
3. Speak or trigger demo:
   > *"வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?"*
4. **Result**:
   - **Transcript**: *வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?*
   - **Translation**: *നമസ്കാരം, സുഖമാണോ?*
   - **Latency Meter**: Displays ~1.65s (Sub-3s SLA).
   - **Audio Output**: Synthesizes and streams Malayalam audio.

### Scenario 2: South Indian Entity Lock Shield
1. Speak a sentence with proper nouns and numbers:
   > *"அருணிடம் 5 புத்தகங்கள் உள்ளன."*
2. **Result**:
   - **Entity Inspector**: Displays `[🔒 அருணிடம் (PERSON)]` and `[🔒 5 (NUMBER)]`.
   - **Translation**: *അരുണിന്റെ കൈയിൽ 5 പുസ്തകങ്ങളുണ്ട്.* (Preserves *Arun* and *5*).

### Scenario 3: Telugu ⇄ Tamil
1. Select **Source**: `Telugu (తెలుగు)` and **Target**: `Tamil (தமிழ்)`.
2. Speak: *"నమస్కారం, మీరు ఎలా ఉన్నారు?"*
3. **Translation**: *வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?*

### Scenario 4: Kannada ⇄ Malayalam
1. Select **Source**: `Kannada (ಕನ್ನಡ)` and **Target**: `Malayalam (മലയാളം)`.
2. Speak: *"ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?"*
3. **Translation**: *നമസ്കാരം, സുഖമാണോ?*

### Scenario 5: Multilingual Pedagogy PDF Studio
1. In the **Multilingual Pedagogy Studio** section:
   - Click **Generate Flashcards PDF** -> Instant download of 2x4 printable bilingual vocabulary cards (Tamil ⇄ Malayalam).
   - Click **Generate Numeracy PDF** -> Instant download of counting & handwriting trace worksheet.
   - Click **Generate Literacy PDF** -> Instant download of word-matching literacy sheet.

---

## 6. Testing & Acceptance Suite

Run the full automated test suite (22 acceptance tests):
```powershell
$env:PYTHONPATH="."
python -m pytest -v
```

Run system acceptance verification script:
```powershell
$env:PYTHONPATH="."
python scripts/verify_setup.py
```

Frontend production build check:
```powershell
cd frontend
npm run build
```

---

## 7. Model Capabilities & Backend Switching

### Running with Mock Mode (Instant Zero-Download Testing)
```env
MOCK_MODE=true
DEMO_MODE=true
```

### Running with Real AI Models (Local GPU / Production Server)
```env
MOCK_MODE=false
DEMO_MODE=false
ASR_BACKEND=faster_whisper
NMT_BACKEND=indictrans2
TTS_BACKEND=indic_tts
```
Download models ahead of time:
```powershell
python scripts/download_models.py --backend all
```

---

## 8. License

This project is licensed under the MIT License.
