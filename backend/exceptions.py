"""
Custom Exception hierarchy for TRANSLARA.
"""
from __future__ import annotations

from typing import Optional


class TranslaraError(Exception):
    """Base exception for all domain errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class ASRError(TranslaraError):
    def __init__(self, message: str, code: str = "ASR_ERROR", details: Optional[dict] = None):
        super().__init__(message, code=code, details=details)


class ASRUnavailableError(ASRError):
    def __init__(self, message: str = "ASR backend is unavailable", details: Optional[dict] = None):
        super().__init__(message, code="ASR_UNAVAILABLE", details=details)


class NMTError(TranslaraError):
    def __init__(self, message: str, code: str = "NMT_ERROR", details: Optional[dict] = None):
        super().__init__(message, code=code, details=details)


class NMTUnavailableError(NMTError):
    def __init__(self, message: str = "NMT backend is unavailable", details: Optional[dict] = None):
        super().__init__(message, code="NMT_UNAVAILABLE", details=details)


class UnsupportedLanguagePairError(NMTError):
    def __init__(self, src: str, tgt: str, details: Optional[dict] = None):
        super().__init__(
            f"Translation for {src.upper()} -> {tgt.upper()} is not currently supported by the configured backend.",
            code="UNSUPPORTED_LANGUAGE_PAIR",
            details=details or {"source_lang": src, "target_lang": tgt},
        )


class TTSError(TranslaraError):
    def __init__(self, message: str, code: str = "TTS_ERROR", details: Optional[dict] = None):
        super().__init__(message, code=code, details=details)


class TTSUnavailableError(TTSError):
    def __init__(self, message: str = "TTS backend is unavailable", details: Optional[dict] = None):
        super().__init__(message, code="TTS_UNAVAILABLE", details=details)


class EntityLockError(TranslaraError):
    def __init__(self, message: str, code: str = "ENTITY_LOCK_ERROR", details: Optional[dict] = None):
        super().__init__(message, code=code, details=details)


class OfflineCacheMissError(TranslaraError):
    def __init__(self, message: str = "Requested phrase not found in offline cache", details: Optional[dict] = None):
        super().__init__(message, code="OFFLINE_PHRASE_NOT_FOUND", details=details)


class PedagogyError(TranslaraError):
    def __init__(self, message: str, code: str = "PEDAGOGY_ERROR", details: Optional[dict] = None):
        super().__init__(message, code=code, details=details)


class FontNotFoundError(PedagogyError):
    def __init__(self, message: str = "Required font file not found for script", details: Optional[dict] = None):
        super().__init__(message, code="FONT_NOT_FOUND", details=details)
