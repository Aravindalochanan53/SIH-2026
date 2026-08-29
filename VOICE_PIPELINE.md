# TRANSLARA — Voice & Real-Time Speech Pipeline

## 1. Speech Streaming Pipeline
TRANSLARA provides full-duplex, low-latency ($<3.0\text{s}$) speech-to-speech translation over WebSocket.

```
Browser Microphone (navigator.mediaDevices.getUserMedia)
                 ↓
      16kHz PCM16 Raw Stream
                 ↓
     WebSocket (/ws/live-stream)
                 ↓
     Streaming VAD (Voice Activity Detection)
                 ↓
     ASR (Faster-Whisper / IndicConformer)
                 ↓
     Source Language Transcript
                 ↓
     Entity Lock Masking (⟦ENT0⟧)
                 ↓
     NMT Translation (Generic Source -> Target)
                 ↓
     Entity Restoration & Script Validation
                 ↓
     Target Language TTS (IndicTTS / VITS)
                 ↓
     ~200ms PCM Audio Chunks streamed back over WebSocket
```

---

## 2. WebSocket Protocol (`/ws/live-stream`)

### Client-to-Server Messages
1. **Start Session:**
   ```json
   {
     "type": "start",
     "source_language": "ta",
     "target_language": "ml",
     "sample_rate": 16000
   }
   ```
2. **Audio Frames:** Send raw binary PCM16 bytes (16000Hz, 16-bit, mono) or Base64 chunks.
3. **Stop Session:**
   ```json
   { "type": "stop" }
   ```

### Server-to-Client Messages
1. **Live Transcript:**
   ```json
   {
     "type": "transcript",
     "transcript": "வணக்கம்",
     "source_lang": "ta"
   }
   ```
2. **Translation & Metadata:**
   ```json
   {
     "type": "translation",
     "transcript": "வணக்கம்",
     "translation": "നമസ്കാരം",
     "source_lang": "ta",
     "target_lang": "ml",
     "latency_ms": 12.4
   }
   ```
3. **Streaming Audio Chunks:**
   ```json
   {
     "type": "audio_chunk",
     "sequence": 0,
     "data": "<base64_encoded_pcm>"
   }
   ```
