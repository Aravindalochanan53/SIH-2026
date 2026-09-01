"""
TRANSLARA — Main FastAPI Application & Real-Time WebSocket Streaming Server.
Connected to Microsoft SQL Server (MSSQL) with local SQLite offline cache fallback.
"""
from __future__ import annotations

import base64
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.api import cache, chat, health, languages, pedagogy, translation, video, voice
from backend.auth import router as auth_router
from backend.cache.database import init_db as init_cache_db
from backend.cache.seed_cache import seed_all as seed_cache_all
from backend.config import settings
from backend.database.connection import init_db as init_main_db
from backend.database.seed import seed_database
from backend.ml_engine.audio_processor import AudioProcessor
from backend.ml_engine.pipeline import run_pipeline, stream_tts, warm_up
from backend.ml_engine.vad import StreamingVAD
from backend.pedagogy.fonts import register_all_fonts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Initializing TRANSLARA Backend Server...")

    # 1. Initialize Primary MSSQL Database & Local Offline Cache
    try:
        init_main_db()
        l_cnt, p_cnt = seed_database()
        logger.info(f"TRANSLARA Primary Database initialized (seeded {l_cnt} languages, {p_cnt} phrases).")
    except Exception as e:
        logger.warning(f"Primary database initialization notice ({e}); running with offline resilience.")

    try:
        init_cache_db()
        cp_cnt, ce_cnt = seed_cache_all()
        logger.info(f"TRANSLARA Offline Cache initialized (seeded {cp_cnt} phrases, {ce_cnt} entities).")
    except Exception as e:
        logger.warning(f"Offline cache notice: {e}")

    # 2. Register Indian Language Fonts
    try:
        register_all_fonts()
    except Exception as e:
        logger.warning(f"Font registration notice: {e}")

    # 3. Warm-up AI Pipeline
    await warm_up()

    logger.info(
        f"TRANSLARA ready! [MOCK_MODE={settings.mock_mode}, DEMO_MODE={settings.demo_mode}]"
    )
    yield
    logger.info("TRANSLARA shutting down.")


# Create FastAPI App
app = FastAPI(
    title="TRANSLARA API",
    description="Real-Time Multilingual Speech Translation, Video Engine & AI Pedagogy Assistant with MSSQL",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(health.router)
app.include_router(languages.router)
app.include_router(translation.router)
app.include_router(voice.router)
app.include_router(video.router)
app.include_router(chat.router)
app.include_router(pedagogy.router)
app.include_router(cache.router)


@app.get("/")
async def root():
    return {
        "project": "TRANSLARA",
        "description": "Real-Time Multilingual Speech Translation, Video Engine & Vernacular Learning",
        "docs": "/docs",
        "health": "/health",
        "languages": "/api/languages",
        "capabilities": "/api/capabilities",
        "auth": "/api/auth",
    }


# ====================================================================== #
# Real-Time WebSocket Streaming Endpoint
# ====================================================================== #

@app.websocket("/ws/live-stream")
async def live_stream_websocket(websocket: WebSocket):
    """
    Bi-directional streaming WebSocket:
    - Receives PCM16 16kHz audio frames from browser microphone
    - Runs streaming VAD -> ASR -> Entity Lock -> NMT -> Entity Restoration
    - Streams live transcript, translation metadata, and chunked TTS audio back to client
    - Does NOT store continuous raw audio chunks in database; only stores finished transcripts
    """
    await websocket.accept()
    logger.info("WebSocket client connected to TRANSLARA Speech Bridge")

    vad = StreamingVAD(
        aggressiveness=settings.vad_aggressiveness,
        tail_silence_ms=settings.vad_tail_silence_ms,
        min_utterance_ms=settings.vad_min_utterance_ms,
        max_utterance_ms=settings.vad_max_utterance_ms,
    )

    source_lang = settings.source_language
    target_lang = settings.default_target_language
    session_id = f"ws_{id(websocket)}"

    try:
        # Handshake greeting
        await websocket.send_text(
            json.dumps({
                "type": "connected",
                "message": "Connected to TRANSLARA Real Speech Bridge",
                "source_lang": source_lang,
                "target_lang": target_lang,
                "sample_rate": 16000,
            })
        )

        while True:
            msg = await websocket.receive()

            # Handle JSON Control Messages
            if "text" in msg and msg["text"]:
                try:
                    payload = json.loads(msg["text"])
                    m_type = payload.get("type")

                    if m_type in ("start", "start_session"):
                        source_lang = payload.get("source_language") or payload.get("source_lang", source_lang)
                        target_lang = payload.get("target_language") or payload.get("target_lang", target_lang)
                        vad.reset()
                        logger.info(f"Real Speech Session Started: {source_lang} -> {target_lang}")
                        await websocket.send_text(
                            json.dumps({
                                "type": "session_started",
                                "source_lang": source_lang,
                                "target_lang": target_lang,
                            })
                        )

                    elif m_type in ("stop", "stop_session"):
                        logger.info("Real Speech Session Stopped by client")
                        buffered_speech = vad.flush()
                        if buffered_speech:
                            await _process_speech_and_respond(
                                websocket, buffered_speech, source_lang, target_lang, session_id
                            )
                        await websocket.send_text(json.dumps({"type": "session_stopped"}))

                    elif m_type == "audio_chunk" and "audio" in payload:
                        # Base64-encoded audio chunk fallback
                        raw_bytes = base64.b64decode(payload["audio"])
                        utterances = vad.process_chunk(raw_bytes)
                        for utterance_pcm in utterances:
                            await _process_speech_and_respond(
                                websocket, utterance_pcm, source_lang, target_lang, session_id
                            )

                except json.JSONDecodeError:
                    pass

            # Handle Binary Audio Frames (PCM16 16kHz mono)
            elif "bytes" in msg and msg["bytes"]:
                raw_bytes = msg["bytes"]
                utterances = vad.process_chunk(raw_bytes)

                for utterance_pcm in utterances:
                    await _process_speech_and_respond(
                        websocket, utterance_pcm, source_lang, target_lang, session_id
                    )

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected ({session_id})")
    except Exception as e:
        logger.error(f"WebSocket processing error: {e}")
        try:
            await websocket.send_text(
                json.dumps({"type": "error", "message": f"Server processing error: {str(e)}"})
            )
        except Exception:
            pass


async def _process_speech_and_respond(
    ws: WebSocket,
    speech_pcm: bytes,
    source_lang: str,
    target_lang: str,
    session_id: str,
) -> None:
    """Run pipeline on detected utterance and stream response."""
    normalized_pcm = AudioProcessor.normalize_pcm16(speech_pcm)

    result = await run_pipeline(
        pcm16_audio=normalized_pcm,
        source_lang=source_lang,
        target_lang=target_lang,
        session_id=session_id,
    )

    if result.error or not result.transcript:
        return

    # 1. Send Immediate Live Transcript
    await ws.send_text(
        json.dumps({
            "type": "transcript",
            "transcript": result.transcript,
            "detected_lang": result.detected_lang,
            "source_lang": result.source_lang,
        })
    )

    # 2. Send Translation & Entity Metadata
    meta_msg = {
        "type": "translation",
        "transcript": result.transcript,
        "translation": result.translation,
        "source_lang": result.source_lang,
        "target_lang": result.target_lang,
        "detected_lang": result.detected_lang,
        "entities_locked": [e.model_dump() for e in result.entities_locked],
        "stage_latencies_ms": result.stage_latencies_ms,
        "latency_ms": result.total_latency_ms,
        "offline": result.used_offline_fallback,
        "warning": result.warning,
    }
    await ws.send_text(json.dumps(meta_msg))

    # 3. Stream Synthesized Audio Chunks (~200ms)
    seq = 0
    async for audio_chunk in stream_tts(result.translation, result.target_lang):
        b64_audio = base64.b64encode(audio_chunk).decode("utf-8")
        chunk_msg = {
            "type": "audio_chunk",
            "sequence": seq,
            "sample_rate": 16000,
            "encoding": "pcm_s16le",
            "data": b64_audio,
        }
        await ws.send_text(json.dumps(chunk_msg))
        seq += 1
