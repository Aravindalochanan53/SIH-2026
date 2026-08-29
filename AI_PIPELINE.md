# TRANSLARA — AI Pipeline & Orchestration

## 1. Pipeline Architecture

```
                 TRANSLARA AI
                      │
              AI Orchestrator
                      │
       ┌──────────────┼──────────────┐
       ↓              ↓              ↓
 Language          Speech         Translation
 Detection        Recognition       Engine
       │              │              │
       │         Faster-Whisper   IndicTrans2
       │         IndicConformer   Bhashini
       │         MMS              Custom data
       │              │              │
       └──────────────┼──────────────┘
                      ↓
                 Entity Lock
                      ↓
                Translation
                      ↓
             Translation Validator
                      ↓
                     TTS
```

---

## 2. Pipeline Stages

### Stage 1: Language Detection & Input Routing
- **Module:** `backend/ai/language_detection/detector.py`
- Analyzes Unicode script points to automatically detect Tamil, Telugu, Kannada, Malayalam, Hindi, Santhali, Ho, and Mundari.

### Stage 2: Entity Lock & Shield
- **Module:** `backend/ai/ner/entity_lock.py`
- Identifies proper student/teacher names, numbers, curriculum terms, math symbols, and currencies.
- Masks entities with unique tokens (`⟦ENT0⟧`, `⟦ENT1⟧`) so that translation models do not alter or mistranslate proper nouns and numeric values.

### Stage 3: Neural Machine Translation (NMT)
- **Module:** `backend/ai/translation/registry.py`
- Fallback chain:
  1. Offline verified database cache (for known classroom expressions).
  2. IndicTrans2 / local seq2seq model with FLORES-200 script tags.
  3. Bhashini ULCA API (Government of India).
  4. Hybrid 2-hop semantic pivot engine for low-resource tribal languages (`sat`, `hoc`, `unr`).

### Stage 4: Entity Restoration
- Unmasks tokens back into target language representation while preserving numbers and proper names.

### Stage 5: Translation & Script Validator
- **Module:** `backend/ai/validators/translation_validator.py`
- Validates Unicode script ranges for target language.
- Rejects fake prefixes (e.g. `[ML]`, `[TA]`), empty translations, and source-copy echo errors.

### Stage 6: Text-to-Speech (TTS)
- **Module:** `backend/ai/tts/indic_tts_provider.py`
- Synthesizes 16kHz audio chunks streamed via WebSocket in sub-200ms segments.
