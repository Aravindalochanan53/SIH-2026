# TRANSLARA — Locally Hosted & Trained AI Models

This directory contains our proprietary and locally fine-tuned AI model artifacts for 100% offline inference.

## Structure

```
trained_models/
├── translation/   # Locally fine-tuned NMT transformer models & syntactic grammar weights
├── asr/           # Locally fine-tuned ASR acoustic models (Faster-Whisper / CTranslate2 INT8)
├── ner/           # Locally trained Indian language Named Entity Recognition models & gazetteers
└── tts/           # Locally trained acoustic synthesis voice models & phoneme maps
```

## Zero Cloud Dependencies
All models located here are executed completely locally in memory with CUDA / CPU acceleration. No internet connection or third-party cloud APIs (OpenAI, Gemini, Bhashini, etc.) are accessed.
