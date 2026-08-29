# TRANSLARA — System Architecture Specification

## 1. System Overview
TRANSLARA is a production-grade AI-powered multilingual education and real-time translation platform designed for diverse Indian classrooms.

```
                    TRANSLARA
                         │
             ┌───────────┴───────────┐
             │                       │
        WEB APPLICATION           AI ENGINE
             │                       │
     ┌───────┼────────┐       ┌──────┼─────────┐
     │       │        │       │      │         │
   Text    Voice    Video    ASR   NMT       TTS
     │       │        │       │      │         │
     └───────┴────────┴───────┴──────┴─────────┘
                         │
                  AI ORCHESTRATOR
                         │
                 ┌───────┴───────┐
                 │               │
               MSSQL       Offline Cache
```

---

## 2. Core Operational Layers

### 1. Web Application (Frontend)
- **Framework:** React 18, Vite, TypeScript, Tailwind CSS.
- **Design System:** English-only clean UI, light modern education workspace theme, responsive HUD layout.
- **Microphone System:** Native `navigator.mediaDevices.getUserMedia()` with 16kHz PCM audio streaming.

### 2. AI Engine & Pipeline
- **ASR:** Faster-Whisper (INT8/float16 CTranslate2), IndicConformer & Meta MMS integration hooks.
- **NER / Entity Shield:** Dynamic gazetteer + regex entity masking (`⟦ENT0⟧`) preventing name/number distortion.
- **NMT Translation:** AI4Bharat IndicTrans2 FLORES-200, Bhashini ULCA API, and 2-hop semantic pivot routing for Santhali (`sat`), Ho (`hoc`), and Mundari (`unr`).
- **Translation Validator:** Rejects fake translations, source echo, and verifies Unicode script purity.
- **TTS:** IndicTTS & VITS local synthesis for real-time speech streaming.

### 3. Database Layer
- **Relational Storage:** Microsoft SQL Server (MSSQL) with automatic fallback to local SQLite for portable operation.
- **ORM:** SQLAlchemy with clean repository patterns (`TranslationRepository`, `PhraseRepository`, `VideoRepository`, `ChatRepository`, `PedagogyRepository`).

---

## 3. Supported Languages
| Language | Code | Script | Region |
| :--- | :--- | :--- | :--- |
| **English** | `en` | Latin | Pan-Indian / Global |
| **Tamil** | `ta` | Tamil (`0x0B80–0x0BFF`) | South India (Tamil Nadu) |
| **Malayalam** | `ml` | Malayalam (`0x0D00–0x0D7F`) | South India (Kerala) |
| **Telugu** | `te` | Telugu (`0x0C00–0x0C7F`) | South India (AP / Telangana) |
| **Kannada** | `kn` | Kannada (`0x0C80–0x0CFF`) | South India (Karnataka) |
| **Hindi** | `hi` | Devanagari (`0x0900–0x097F`) | North India |
| **Santhali** | `sat` | Ol Chiki (`0x1C50–0x1C7F`) | Tribal (Jharkhand / WB / Odisha) |
| **Ho** | `hoc` | Devanagari / Warang Citi | Tribal (Jharkhand / Odisha) |
| **Mundari** | `unr` | Devanagari / Mundari Bani | Tribal (Jharkhand) |
