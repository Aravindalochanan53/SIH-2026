# TRANSLARA AI — 100% Local AI Model Architecture & Training Guide

TRANSLARA runs **entirely on locally hosted and fine-tuned AI models**. It requires **zero external cloud AI APIs** (no OpenAI, Gemini, Claude, Bhashini, or third-party inference services) and operates 100% offline.

---

## 1. Directory Structure of Local Models

```text
trained_models/
├── translation/   # Locally fine-tuned translation models & neural grammar engine
├── asr/           # Locally fine-tuned Faster-Whisper / INT8 acoustic models
├── ner/           # Locally trained entity extraction models & Indian language gazetteers
└── tts/           # Locally trained multi-pitch acoustic synthesizer
```

---

## 2. Automatic Hardware Detection & Memory Management

On startup, `backend/app/models/model_loader.py`:
- Detects available compute hardware automatically (**CUDA GPU** or optimized **INT8 CPU**).
- Loads all models once into memory during server startup.
- Reuses loaded models across all requests (no reload overhead).
- Operates 100% offline without network calls.

---

## 3. How to Train / Fine-Tune Local Models

The training pipeline is decoupled from inference and saves model artifacts directly to `trained_models/`:

### A. Fine-Tune Local Translation Model (NMT)
```powershell
python -m training.train_translation --config config/training.yaml
```
- Trains on Indian language parallel corpora (Tamil, Malayalam, Hindi, Telugu, Kannada, English, Santhali, etc.).
- Saves fine-tuned model artifacts to `trained_models/translation/`.

### B. Fine-Tune Local Speech Recognition Model (ASR)
```powershell
python -m training.train_asr --config config/training.yaml
```
- Fine-tunes speech recognition on Indian language classroom audio datasets.
- Saves model artifacts to `trained_models/asr/`.

### C. Train Local Named Entity Recognition Model (NER)
```powershell
python -m training.train_ner --config config/training.yaml
```
- Trains token classification for student names, math expressions, currency, and places.
- Saves model artifacts to `trained_models/ner/`.

### D. Train Local Speech Synthesis Model (TTS)
```powershell
python -m training.train_tts --config config/training.yaml
```
- Trains local acoustic synthesis voices for Indian languages.
- Saves model artifacts to `trained_models/tts/`.

---

## 4. Running Backend & Local AI Endpoints

From the project root:
```powershell
python -m uvicorn app.main:app --reload
```

### Local AI Endpoints:
- **`POST /api/local/translation/translate`** — Local text translation
- **`POST /api/local/speech/transcribe`** — Local audio transcription
- **`POST /api/local/ner/extract`** — Local entity extraction and token shielding
- **`GET /api/local/ai/status`** — Local AI engine status & device details
- **`GET /api/local/ai/models`** — List loaded local model artifacts

---

## 5. Verifying 100% Offline AI Execution

Run the standalone verification script to test all local AI subsystems without internet:
```powershell
python scripts/test_local_ai.py
```
