# TRANSLARA AI — Model Setup & Installation Guide

This guide explains how to configure and deploy local models or API integrations for TRANSLARA AI.

---

## 1. Automatic Device Detection

TRANSLARA automatically detects hardware capabilities on startup:
- **CUDA GPU:** Automatically loads models with `float16` precision and GPU acceleration.
- **CPU:** Automatically uses `int8` quantization for optimal latency and low memory usage.

---

## 2. Setting Up IndicTrans2 (Local NMT)

### Model Repositories
- **Indic-to-Indic / English:** `ai4bharat/indictrans2-indic-indic-dist-320M`
- **English-to-Indic:** `ai4bharat/indictrans2-en-indic-dist-320M`
- **Indic-to-English:** `ai4bharat/indictrans2-indic-en-dist-320M`

### Installation & Download
```bash
pip install torch transformers sentencepiece sacremoses
```
In `.env`:
```env
MOCK_MODE=false
NMT_BACKEND=indictrans2
INDICTRANS2_MODEL_ID=ai4bharat/indictrans2-indic-indic-dist-320M
```

---

## 3. Setting Up Faster-Whisper (ASR)

### Installation
```bash
pip install faster-whisper
```
In `.env`:
```env
ASR_BACKEND=faster_whisper
WHISPER_MODEL_SIZE=small
WHISPER_DEVICE=auto
WHISPER_COMPUTE_TYPE=int8
```

---

## 4. Setting Up Government of India Bhashini ULCA API

If you have credentials from [Bhashini](https://bhashini.gov.in):
In `.env`:
```env
NMT_BACKEND=bhashini_ulca
BHASHINI_USER_ID=your_user_id
BHASHINI_INFERENCE_API_KEY=your_inference_api_key
```

---

## 5. Running the Quality & Accuracy Benchmark

To evaluate translation quality, BLEU score, script purity, and entity preservation across all language pairs:

```bash
python training/eval.py
```
